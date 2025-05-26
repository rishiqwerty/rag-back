from typing import Any, List
from pydantic import BaseModel, EmailStr


class TaskStatusCreate(BaseModel):
    file_name: str
    user_email: EmailStr


class QuestionRequest(BaseModel):
    question: str
    task_id: str


class AggregationResult(BaseModel):
    count: int
    maximum: int
    minimum: int
    mean: float
    total: int
    max_user_details: List[Any]
    min_user_details: List[Any]


class AggregationResponse(BaseModel):
    task_id: str
    field: str
    output: AggregationResult
