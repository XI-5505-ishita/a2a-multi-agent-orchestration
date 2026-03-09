# from dotenv import load_dotenv
# load_dotenv()
# from typing import TypedDict
# from langgraph.graph import StateGraph, END
# from langchain_openai import ChatOpenAI
# from langchain_core.messages import HumanMessage

# from langfuse import observe, get_client
# from langfuse.langchain import CallbackHandler
# langfuse_handler = CallbackHandler()


# langfuse = get_client()


# llm = ChatOpenAI(model="gpt-4o-mini",
#                  callbacks=[langfuse_handler])


# class GraphState(TypedDict):
#     input_text: str
#     cleaned_text: str
#     summary: str


# def clean_text(state: GraphState):
#     return {"cleaned_text": state["input_text"].strip()}


# def generate_summary(state: GraphState):
#     prompt = f"""
# Summarize the following text.
# Reduce redundancy and compress the information clearly.

# Text:
# {state['cleaned_text']}
# """
#     response = llm.invoke([HumanMessage(content=prompt)])
#     return {"summary": response.content}


# builder = StateGraph(GraphState)
# builder.add_node("clean_text", clean_text)
# builder.add_node("generate_summary", generate_summary)

# builder.set_entry_point("clean_text")
# builder.add_edge("clean_text", "generate_summary")
# builder.add_edge("generate_summary", END)

# graph = builder.compile()
# @observe()
# def run_summarizer(text: str):
    
#     result = graph.invoke({"input_text": text})
        
#     return result["summary"]

from dotenv import load_dotenv
load_dotenv()

from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool

from langfuse import observe
from langfuse.langchain import CallbackHandler
import os

langfuse_handler = CallbackHandler()

api_key= os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    api_key=api_key,
    callbacks=[langfuse_handler]
)

# =========================
# STATE
# =========================

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

# =========================
# TOOLS
# =========================

@tool
def summarize_text(text: str):
    """Summarize the given text clearly and concisely."""
    prompt = f"""
Summarize the following text.
Reduce redundancy and compress the information clearly.

Text:
{text}
"""
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content

tools = [summarize_text]

llm_with_tools = llm.bind_tools(tools)

# =========================
# AGENT NODE
# =========================

def agent_node(state: AgentState):
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}

# =========================
# GRAPH
# =========================

builder = StateGraph(AgentState)

builder.add_node("agent", agent_node)
builder.add_node("tools", ToolNode(tools))

builder.set_entry_point("agent")

builder.add_conditional_edges(
    "agent",
    lambda state: "tools" if state["messages"][-1].tool_calls else END
)

builder.add_edge("tools", "agent")

graph = builder.compile()

# =========================
# RUN FUNCTION
# =========================

@observe()
def run_summarizer(text: str):
    result = graph.invoke({
        "messages": [HumanMessage(content=text)]
    })
    return result["messages"][-1].content