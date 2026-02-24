from fastapi import FastAPI
from pydantic import BaseModel
from orchestrator_agent.client import call_agent

app = FastAPI(title="Orchestrator Agent")

SUMMARIZER_URL = "http://localhost:8101"
TRANSLATOR_URL = "http://localhost:8102"


class ExecuteRequest(BaseModel):
    input_text: str
    task: str


@app.post("/execute")
async def execute(request: ExecuteRequest):

    if request.task == "summarize":
        result = await call_agent(SUMMARIZER_URL, request.input_text)

    elif request.task == "translate":
        result = await call_agent(TRANSLATOR_URL, request.input_text)

    else:
        return {"error": "Invalid task"}

    return {"final_output": result}