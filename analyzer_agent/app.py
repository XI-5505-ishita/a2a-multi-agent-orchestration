from fastapi import FastAPI, BackgroundTasks
from shared.schema import (
    TaskCreateRequest,
    TaskCreateResponse,
    TaskStatusResponse,
    generate_task_id,
)
from shared.task_store import create_task, update_task, get_task
from analyzer_agent.graph import run_agent

app = FastAPI(title="Analyzer Agent")


@app.get("/agent-card")
def agent_card():
    return {
        "name": "AnalyzerAgent",
        "version": "1.0",
        "capabilities": ["analysis"],
        "endpoints": {"create_task": "/create-task", "task_status": "/task/{task_id}"},
    }

x=run_agent()
import asyncio


# def process_task(task_id: str, text: str):
#     try:
#         result = asyncio.run(run_agent(text))  # ✅ run async function properly
#         update_task(task_id, status="completed", result=result)
#     except Exception as e:
#         update_task(task_id, status="failed", result=str(e))

import asyncio


def process_task(task_id: str, text: str):
    try:
        update_task(task_id, status="running", result=None)

        response = asyncio.run(run_agent(text))

        # Extract the final AI response text
        result_text = response["messages"][-1].content

        update_task(task_id, status="completed", result=result_text)

    except Exception as e:
        update_task(task_id, status="failed", result=str(e))


@app.post("/create-task", response_model=TaskCreateResponse)
def create_analysis_task(request: TaskCreateRequest, background_tasks: BackgroundTasks):

    task_id = generate_task_id()

    create_task(task_id, request.input_text)

    background_tasks.add_task(process_task, task_id, request.input_text)

    return TaskCreateResponse(task_id=task_id, status="pending")


@app.get("/tasks/{task_id}", response_model=TaskStatusResponse)
def get_task_status(task_id: str):

    task = get_task(task_id)

    return TaskStatusResponse(
        task_id=task_id, status=task["status"], result=task["result"]
    )
