from dotenv import load_dotenv
load_dotenv()
import httpx
import asyncio
import json
import re

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langfuse import observe, get_client
from langfuse.langchain import CallbackHandler
langfuse_handler = CallbackHandler()
langfuse=get_client()



SUMMARIZER_URL = "http://localhost:8101"
TRANSLATOR_URL = "http://localhost:8102"

llm = ChatOpenAI(model="gpt-4o-mini",
                 callbacks=[langfuse_handler])

AGENTS = [
    {
        "name": "SummarizerAgent",
        "url": SUMMARIZER_URL,
        "capabilities": ["summarization"]
    },
    {
        "name": "TranslatorAgent",
        "url": TRANSLATOR_URL,
        "capabilities": ["translation"]
    }
]


@observe()
def plan_execution(query: str):
    agent_descriptions = "\n".join(
        [f"{agent['name']} → {agent['capabilities']}" for agent in AGENTS]
    )

    prompt = f"""
You are a host orchestration agent.

Available agents:
{agent_descriptions}

Return ONLY a valid JSON list of agent names in execution order.
No explanation.
No markdown.
No code blocks.

Example:
["SummarizerAgent", "TranslatorAgent"]

User Query:
{query}
"""

    response = llm.invoke([HumanMessage(content=prompt)])
    raw_output = response.content.strip()

    raw_output = re.sub(r"```.*?```", "", raw_output, flags=re.DOTALL)

    try:
        return json.loads(raw_output)
    except json.JSONDecodeError:
        print("LLM returned invalid JSON:", raw_output)
        return []


@observe()
async def call_agent(base_url, text):
    async with httpx.AsyncClient() as client:

        # Create task
        create_resp = await client.post(
            f"{base_url}/create-task",
            json={"input_text": text}
        )

        create_data = create_resp.json()
        task_id = create_data.get("task_id")

        if not task_id:
            return create_data

        # Poll until completed
        while True:
            status_resp = await client.get(
                f"{base_url}/task/{task_id}"
            )

            status_data = status_resp.json()

            if status_data["status"] == "completed":
                return status_data["result"]

            await asyncio.sleep(0.5)


@observe()
async def main():
    user_query = input("Enter your query: ")

    execution_plan = plan_execution(user_query)

    print("Execution Plan:", execution_plan)

    current_input = user_query

    for agent_name in execution_plan:

        selected_agent = next(
            (agent for agent in AGENTS if agent["name"] == agent_name),
            None
        )

        if not selected_agent:
            print(f"Agent {agent_name} not found.")
            return

        print(f"\nCalling {agent_name}...")
        current_input = await call_agent(
            selected_agent["url"],
            current_input
        )

    print("\nFinal Output:\n", current_input)


if __name__ == "__main__":
    asyncio.run(main())