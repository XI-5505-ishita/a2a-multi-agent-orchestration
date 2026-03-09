from dotenv import load_dotenv

load_dotenv()

import os
import json
import re
import asyncio
import httpx

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

api_key = os.getenv("OPENAI_API_KEY")

SUMMARIZER_URL = os.getenv("SUMMARIZER_URL", "http://127.0.0.1:8101")
TRANSLATOR_URL = os.getenv("TRANSLATOR_URL", "http://127.0.0.1:8102")
ANALYZER_URL = os.getenv("ANALYZER_URL", "http://127.0.0.1:8103")

AGENTS = [
    {
        "name": "SummarizerAgent",
        "url": SUMMARIZER_URL,
        "capabilities": ["summarization"],
    },
    {"name": "TranslatorAgent", "url": TRANSLATOR_URL, "capabilities": ["translation"]},
    {"name": "AnalyzerAgent", "url": ANALYZER_URL, "capabilities": ["analysis"]},
]

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=api_key)


def plan_execution(query: str):
    agent_descriptions = "\n".join(
        f"{agent['name']} → {agent['capabilities']}" for agent in AGENTS
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
            f"{base_url}/create-task", json={"input_text": str(text)}
        )
        print(create_resp.json())

        create_data = create_resp.json()
        task_id = create_data.get("task_id") or create_data.get("id")

        if not task_id:
            return create_data

        while True:
            status_resp = await client.get(f"{base_url}/tasks/{task_id}")
            print("STATUS CODE:", status_resp.status_code)
            print("RAW RESPONSE:", status_resp.text)

            status_data = status_resp.json()

            if status_data["status"] == "completed":
                return str(status_data.get("result", ""))

            await asyncio.sleep(0.5)
