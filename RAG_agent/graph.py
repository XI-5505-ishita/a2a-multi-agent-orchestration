
from typing import List, Dict
import os
from dotenv import load_dotenv
import pdfplumber
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.tools import tool, StructuredTool
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

# --- OpenTelemetry Imports ---
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter

load_dotenv() 

provider = TracerProvider()
processor = SimpleSpanProcessor(ConsoleSpanExporter())
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)

# GLOBAL EMBEDDING MODEL
embedder = SentenceTransformer("models/all-MiniLM-L6-v2-sbert")
embedder.max_seq_length = 256

chroma_client = chromadb.Client(
    Settings(
        persist_directory="./chroma_db",
        is_persistent=True,
        anonymized_telemetry=False
    )
)

collection = chroma_client.get_or_create_collection(
    name="otel_docs",
    metadata={"hnsw:space": "cosine"}
)


@tool
def extract_pdf(pdf_path: str) -> List[Dict]:
    """Extract text from each page of a PDF."""
    pages_data = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text:
                pages_data.append({"text": text, "page_no": i + 1})
    return pages_data

@tool
def chunk_pdf(pages_data: List[Dict]) -> List[Dict]:
    """Split PDF pages into chunks."""
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    chunks = []
    for entry in pages_data:
        docs = splitter.create_documents([entry["text"]])
        for doc in docs:
            chunks.append({
                "chunk_id": len(chunks),
                "content": doc.page_content,
                "metadata": {"page": entry["page_no"]}
            })
    return chunks

@tool
def store_chunks_in_chroma(chunks: List[Dict]) -> str:
    """Store chunks in ChromaDB."""
    if collection.count() > 0:
        return "Data already exists in ChromaDB."
    texts = [c["content"] for c in chunks]
    embeddings = embedder.encode(texts, normalize_embeddings=True, convert_to_numpy=True)
    ids = [f"chunk_{i}" for i in range(len(chunks))]
    metadatas = [{"page": c["metadata"]["page"]} for c in chunks]
    collection.add(ids=ids, documents=texts, embeddings=embeddings.tolist(), metadatas=metadatas)
    return f"Stored {len(chunks)} chunks."

#Manuaaly tool create krre h, second way of creating tool
def retrieve_chunks_logic(query: str) -> str: 
    """Search the document for relevant information."""
    #retrival ke traces ke liye span create krre h, jisme query bhi attach krre h
    with tracer.start_as_current_span("chroma_retrieve_tool") as span:
        span.set_attribute("search.query", query)
        
        query_embedding = embedder.encode([query], normalize_embeddings=True, convert_to_numpy=True)
        # Fetching 3 chunks as requested
        results = collection.query(query_embeddings=query_embedding.tolist(), n_results=3)
        
        if not results["documents"] or len(results["documents"][0]) == 0:
            return "No information found."

        output_for_llm = "I found 3 chunks. Use these to answer:\n\n"
        for i, content in enumerate(results["documents"][0]):
            page = results["metadatas"][0][i]["page"]
            # Trace the full content
            span.set_attribute(f"retrieved_chunk_{i}_page", page)
            span.set_attribute(f"retrieved_chunk_{i}_content", content)
            # Send content to LLM
            output_for_llm += f"--- Result {i+1} (Page {page}) ---\n{content}\n\n"
        
        return output_for_llm.strip()
# Explicitly defining the tool to avoid AttributeError
retrieve_chunks = StructuredTool.from_function(
    func=retrieve_chunks_logic,
    name="retrieve_chunks",
    description="Use this to search the document for answers. Input should be a search query."
)

# RAG AGENT 
class RAGAgent:
    def __init__(self, pdf_path: str):
        print("Pre-processing document...")
        pages = extract_pdf.invoke({"pdf_path": pdf_path})
        chunks = chunk_pdf.invoke({"pages_data": pages})
        print(store_chunks_in_chroma.invoke({"chunks": chunks}))
        #we are not usinf another tools because , it gets too much data(10 chunks content)
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.tools = [retrieve_chunks]

        # The template MUST have {tools}, {tool_names}, and {agent_scratchpad}
        template = """Answer the following questions. You have access to the following tools:

{tools}

To use a tool, you MUST use this format:
Question: {input}
Thought: I should search for [keywords]
Action: retrieve_chunks
Action Input: [keywords]
Observation: [tool output]
... (this Thought/Action/Action Input/Observation can repeat)
Thought: I now have the answer
Final Answer: [your answer]

Available tools: [{tool_names}]

Begin!

Question: {input}
Thought: {agent_scratchpad}"""

        prompt = PromptTemplate(
            template=template, 
            # tool_names MUST be in this list
            input_variables=["input", "tools", "tool_names", "agent_scratchpad"]
        )

        agent_plan = create_react_agent(self.llm, self.tools, prompt)
        
        self.agent_executor = AgentExecutor(
            agent=agent_plan, 
            tools=self.tools, 
            verbose=True, # isko on krne pr wo thoughts bhi dikhyega
            handle_parsing_errors=True,
            max_iterations=8,
            max_execution_time=60 # 4 allows for the search + processing of 3 chunks
        )
    # ye agent ke traces me dikhayega ki user ne kya query ki, 
    def query(self, user_query: str):
        with tracer.start_as_current_span("agent_full_query") as span:
            span.set_attribute("user.query", user_query)
            response = self.agent_executor.invoke({"input": user_query})
            span.set_attribute("agent.response", str(response["output"]))
            return response

import asyncio

async def run_agent(user_input: str):
    """Async function that can be imported from other files"""

    PDF_FILE = "doc.pdf"

    agent = RAGAgent(PDF_FILE)

    # run the blocking query in a thread so async environments (FastAPI etc.) work
    result = await asyncio.to_thread(agent.query, user_input)

    return result["output"]

# if __name__ == "__main__":
#     import asyncio
    
#     query = "What is Annex B?"
#     result = asyncio.run(run_agent(query))
    
#     print("\nFINAL ANSWER:\n")
#     print(result)