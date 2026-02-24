from dotenv import load_dotenv
load_dotenv()
from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from langfuse import observe, get_client
from langfuse.langchain import CallbackHandler
langfuse_handler = CallbackHandler()


langfuse = get_client()


llm = ChatOpenAI(model="gpt-4o-mini",
                 callbacks=[langfuse_handler])


class GraphState(TypedDict):
    input_text: str
    cleaned_text: str
    summary: str


def clean_text(state: GraphState):
    return {"cleaned_text": state["input_text"].strip()}


def generate_summary(state: GraphState):
    prompt = f"""
Summarize the following text.
Reduce redundancy and compress the information clearly.

Text:
{state['cleaned_text']}
"""
    response = llm.invoke([HumanMessage(content=prompt)])
    return {"summary": response.content}


builder = StateGraph(GraphState)
builder.add_node("clean_text", clean_text)
builder.add_node("generate_summary", generate_summary)

builder.set_entry_point("clean_text")
builder.add_edge("clean_text", "generate_summary")
builder.add_edge("generate_summary", END)

graph = builder.compile()
@observe()
def run_summarizer(text: str):
    
    result = graph.invoke({"input_text": text})
        
    return result["summary"]