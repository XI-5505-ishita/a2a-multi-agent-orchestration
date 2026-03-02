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

langfuse_handler = CallbackHandler()

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    callbacks=[langfuse_handler]
)

# STATE

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

# =========================
# TOOLS
# =========================

@tool
def translate_to_hindi(text: str) -> str:
    """Translate the given text into Hindi."""
    prompt = f"Translate the following text into Hindi:\n\n{text}"
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content

tools = [translate_to_hindi]

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
def run_translator(text: str):
    result = graph.invoke({
        "messages": [HumanMessage(content=text)]
    })
    return result["messages"][-1].content

