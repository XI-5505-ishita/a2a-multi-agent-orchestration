import re
import os
from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.openai import OpenAIChat


load_dotenv()

def cleaner_tool(transcript: str) -> str:
    """
    Clean transcript before answering queries.
    """

    fillers = ["um", "uh", "you know", "like", "actually", "basically"]

    for word in fillers:
        transcript = re.sub(rf"\b{word}\b", "", transcript, flags=re.IGNORECASE)

    transcript = re.sub(r"\s+", " ", transcript)
    transcript = transcript.replace("\n", " ")
    transcript = transcript.strip()

    return transcript


def query_answer_tool(input_text: str) -> str:
    """
    Answer questions using the transcript.
    The input_text should contain both transcript and user query.
    """

    prompt = f"""
You are a meeting assistant.

Answer the user query ONLY using the transcript below.

If the answer is not present, reply:
"Information not found in transcript."

Input:
{input_text}

Answer:
"""

    return prompt

model = OpenAIChat(
    id="gpt-4o-mini",
    api_key=os.getenv("OPENAI_API_KEY")
)

SYSTEM_PROMPT = """
You are a transcript assistant.

Workflow:
1. Clean transcript using cleaner_tool
2. Use query_answer_tool to answer user question

Rules:
- Answer ONLY from transcript
- Do not hallucinate
"""



transcript_agent = Agent(
    name="transcript_agent",
    model=model,
    description="Answers questions from meeting transcripts.",
    instructions=SYSTEM_PROMPT,
    tools=[
        cleaner_tool,
        query_answer_tool
    ],
    markdown=True
)
async def run_momagent(text: str):
    """Function that can be imported from other files"""

    result = await transcript_agent.arun(text)

    return result.content


# import asyncio

# if __name__ == "__main__":

#     # Path to transcript file
#     file_path = "ts2.txt"

#     # Read the txt file
#     with open(file_path, "r", encoding="utf-8") as f:
#         transcript = f.read()

#     # Run the MOM agent
#     result = asyncio.run(run_momagent(transcript))

#     print("\n===== Minutes of Meeting =====\n")
#     print(result)