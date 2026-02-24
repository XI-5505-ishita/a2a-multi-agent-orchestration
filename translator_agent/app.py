from fastapi import FastAPI, BackgroundTasks
from shared.schema import (
    TaskCreateRequest,
    TaskCreateResponse,
    TaskStatusResponse,
    generate_task_id
)
from shared.task_store import create_task, update_task, get_task
from translator_agent.graph import run_translator

app = FastAPI(title="Translator Agent")


@app.get("/agent-card")
def agent_card():
    return {
        "name": "TranslatorAgent",
        "version": "1.0",
        "capabilities": ["translation"],
        "endpoints": {
            "create_task": "/create-task",
            "task_status": "/task/{task_id}"
        }
    }


def process_task(task_id):
    update_task(task_id, status="running")
    text = get_task(task_id)["input"]

    result = run_translator(text)

    update_task(task_id, status="completed", result=result)


@app.post("/create-task", response_model=TaskCreateResponse)
def create_task_endpoint(request: TaskCreateRequest, background_tasks: BackgroundTasks):
    task_id = generate_task_id()
    create_task(task_id, request.input_text)

    background_tasks.add_task(process_task, task_id)

    return TaskCreateResponse(task_id=task_id, status="pending")


@app.get("/task/{task_id}", response_model=TaskStatusResponse)
def task_status(task_id: str):
    task = get_task(task_id)

    return TaskStatusResponse(
        task_id=task_id,
        status=task["status"],
        result=task["result"]
    )