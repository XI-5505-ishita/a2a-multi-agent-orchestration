from pydantic import BaseModel
from typing import Optional
from uuid import uuid4


class TaskCreateRequest(BaseModel):
    input_text: str


class TaskCreateResponse(BaseModel):
    task_id: str
    status: str


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[str] = None


def generate_task_id():
    return str(uuid4())