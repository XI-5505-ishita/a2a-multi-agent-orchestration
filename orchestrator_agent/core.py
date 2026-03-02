from dotenv import load_dotenv
load_dotenv()

import os
import json
import re
import asyncio
import httpx

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

SUMMARIZER_URL = os.getenv("SUMMARIZER_URL", "http://localhost:8101")
TRANSLATOR_URL = os.getenv("TRANSLATOR_URL", "http://localhost:8102")

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

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


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

User Query:
{query}
"""

    response = llm.invoke([HumanMessage(content=prompt)])
    raw_output = response.content.strip()
    raw_output = re.sub(r"```.*?```", "", raw_output, flags=re.DOTALL)

    try:
        return json.loads(raw_output)
    except json.JSONDecodeError:
        return []


async def call_agent(base_url, text):
    async with httpx.AsyncClient() as client:

        create_resp = await client.post(
            f"{base_url}/create-task",
            json={"input_text": text}
        )

        create_data = create_resp.json()
        task_id = create_data.get("task_id")

        if not task_id:
            return create_data

        while True:
            status_resp = await client.get(
                f"{base_url}/task/{task_id}"
            )

            status_data = status_resp.json()

            if status_data["status"] == "completed":
                return status_data["result"]

            await asyncio.sleep(0.5)