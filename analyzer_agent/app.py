from fastapi import FastAPI, BackgroundTasks
from shared.schema import (
    TaskCreateRequest,
    TaskCreateResponse,
    TaskStatusResponse,
    generate_task_id
)
from shared.task_store import create_task, update_task, get_task
from analyzer_agent.graph import analyzer_tool

app = FastAPI(title="Analyzer Agent")

@app.get("/agent-card")
def agent_card():
    return {
        "name": "AnalyzerAgent",
        "version": "1.0",
        "capabilities": ["analysis"],
        "endpoints": {
            "create_task": "/create-task",
            "task_status": "/task/{task_id}"
        }
    }


def process_task(task_id: str, text: str):
    try:
        result = analyzer_tool(text)
        update_task(task_id, status="completed", result=result)
    except Exception as e:
        update_task(task_id, status="failed", result=str(e))


@app.post("/create-task", response_model=TaskCreateResponse)
def create_analysis_task(request: TaskCreateRequest, background_tasks: BackgroundTasks):

    task_id = generate_task_id()

    create_task(task_id, result=None)

    background_tasks.add_task(process_task, task_id, request.text)

    return TaskCreateResponse(task_id=task_id)


@app.get("/tasks/{task_id}", response_model=TaskStatusResponse)
def get_task_status(task_id: str):

    task = get_task(task_id)

    return TaskStatusResponse(
        task_id=task_id,
        status=task["status"],
        result=task["result"]
    )
