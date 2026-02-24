from dotenv import load_dotenv
load_dotenv()
from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from langfuse import observe, get_client
langfuse=get_client()
from langfuse.langchain import CallbackHandler
langfuse_handler = CallbackHandler()

llm = ChatOpenAI(model="gpt-4o-mini",
                 callbacks=[langfuse_handler])


class GraphState(TypedDict):
    input_text: str
    translated_text: str


def translate_text(state: GraphState):
    prompt = f"Translate this to Hindi:\n{state['input_text']}"
    response = llm.invoke([HumanMessage(content=prompt)])
    return {"translated_text": response.content}


builder = StateGraph(GraphState)
builder.add_node("translate_text", translate_text)

builder.set_entry_point("translate_text")
builder.add_edge("translate_text", END)

graph = builder.compile()

@observe()
def run_translator(text: str):
    
    result = graph.invoke({"input_text": text})
        
    return result["translated_text"]