from fastapi import FastAPI, BackgroundTasks
import asyncio

from shared.schema import (
    TaskCreateRequest,
    TaskCreateResponse,
    TaskStatusResponse,
    generate_task_id,
)

from shared.task_store import create_task, update_task, get_task
from graph import run_momagent


app = FastAPI(
    title="Transcript Query API",
    description="Provide responses to user's query",
    version="1.0"
)


print("RUNNING MOM AGENT APP")
@app.get("/agent-card")
def agent_card():
    return {
        "name": "minutes-agent",
        "version": "1.0",
        "description": "Agent that processes meeting transcripts and answers user queries based strictly on the transcript content.",
        "capabilities": [
            "meeting transcript processing",
            "transcript cleaning and normalization",
            "transcript-based question answering",
            "meeting discussion analysis",
            "information extraction from meeting transcripts"
        ],
        "endpoints": {
            "create-task": "/create-task",
            "task_status": "/tasks/{task_id}"
        }
    }

@app.get("/")
def home():
    return {"message": "Transcript Agent API is running"}

@app.post("/run_momagent")
async def run_momagent_endpoint(request: dict):
    text = request.get("input", "")
    result = await run_momagent(text)
    return {"output": result}


def process_task(task_id: str, text: str):
    try:
        update_task(task_id, status="running", result=None)

        # run async agent inside background task
        result_text = asyncio.run(run_momagent(text))

        update_task(task_id, status="completed", result=result_text)

    except Exception as e:
        update_task(task_id, status="failed", result=str(e))


# ---------------- CREATE TASK ---------------- #

@app.post("/create-task", response_model=TaskCreateResponse)
def create_analysis_task(request: TaskCreateRequest, background_tasks: BackgroundTasks):

    task_id = generate_task_id()

    create_task(task_id, request.input_text)

    background_tasks.add_task(process_task, task_id, request.input_text)

    return TaskCreateResponse(
        task_id=task_id,
        status="pending"
    )



# ---------------- TASK STATUS ---------------- #

@app.get("/tasks/{task_id}", response_model=TaskStatusResponse)
def get_task_status(task_id: str):

    task = get_task(task_id)

    return TaskStatusResponse(
        task_id=task_id,
        status=task["status"],
        result=task["result"]
    )