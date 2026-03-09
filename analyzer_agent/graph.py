from dotenv import load_dotenv

load_dotenv()

from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
import os

api_key = os.getenv("OPENAI_API_KEY")


llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=api_key)


@tool
def analyzer_tool(text: str) -> str:
    """Analyzes text and returns sentiment, tone, key points and summary."""

    prompt = f"""
    Analyze the following text and provide:
    - Sentiment
    - Tone
    - Key Points
    - Summary

    Text:
    {text}
    """

    response = llm.invoke(prompt)
    return response.content


tools = [analyzer_tool]


agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt="""
You are an intelligent analysis agent.

Your job is to:
- Understand the user's request
- Use available tools when necessary
- Return clear and structured responses

If the user asks for text analysis, use the analyzer_tool.
""",
)


async def run_agent(text: str):
    """Function that can be imported from other files"""

    result = await agent.ainvoke({"messages": [{"role": "user", "content": text}]})

    return result["messages"][-1].content


# if __name__ == "__main__":
#     response = agent.invoke({
#         "messages": [
#             {"role": "user", "content": "Analyze this text: The product launch was risky but resulted in massive success."}
#         ]
#     })

#     print(response["messages"][-1]["content"])
