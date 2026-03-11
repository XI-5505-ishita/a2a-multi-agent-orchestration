"""
FastAPI wrapper to APPIFY the RAG Agent.

This API exposes the RAG agent as a service so that an
Orchestrator Agent can discover and call it.
"""

from pydantic import BaseModel
from graph import run_agent

from fastapi import FastAPI, BackgroundTasks
from shared.schema import (
    TaskCreateRequest,
    TaskCreateResponse,
    TaskStatusResponse,
    generate_task_id,
)
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.task_store import create_task, update_task, get_task
#from analyzer_agent.graph import run_agent

# --------------------------------------------------
# Initialize FastAPI
# --------------------------------------------------

app = FastAPI(
    title="RAG Agent API",
    description="Appified RAG Agent using FastAPI",
    version="1.0"
)


# --------------------------------------------------
# Request Schema
# --------------------------------------------------

class QueryRequest(BaseModel):
    query: str


# --------------------------------------------------
# Health Check Endpoint
# --------------------------------------------------

@app.get("/")
def health_check():
    return {
        "status": "running",
        "agent": "rag-document-agent"
    }


# --------------------------------------------------
# Agent Card Endpoint (For Orchestrator Discovery)
# --------------------------------------------------

@app.get("/agent-card")
def agent_card():
    return {
        "name": "rag-document-agent",
        "version": "1.0",
        "capabilities": [
            "document question answering",
            "answer questions from pdf",
            "document knowledge retrieval",
            "rag based document search"
        ],
        "endpoints": {
            "create_task": "/create-task",
            "task_status": "/tasks/{task_id}"
        }
    }

    return agent_card


# --------------------------------------------------
# Main Execution Endpoint
# --------------------------------------------------
import asyncio


def process_task(task_id: str, text: str):
    try:
        print(f"[TASK STARTED] {task_id}")

        update_task(task_id, status="running", result=None)

        print("Running RAG agent...")
        response = asyncio.run(run_agent(text))
        print("Agent response received:", response)

        # Handle different response formats safely
        if isinstance(response, dict) and "messages" in response:
            result_text = response["messages"][-1].content
        else:
            result_text = str(response)

        update_task(task_id, status="completed", result=result_text)

        print(f"[TASK COMPLETED] {task_id}")

    except Exception as e:
        print(f"[TASK FAILED] {task_id} -> {e}")
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

    print("TASK STORE STATE:", task)

    return TaskStatusResponse(
        task_id=task_id,
        status=task["status"],
        result=task["result"]
    )
