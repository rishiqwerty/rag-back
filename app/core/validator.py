from typing import Any, List, Optional, Union
from pydantic import BaseModel, EmailStr


class TaskStatusCreate(BaseModel):
    file_name: str
    user_email: EmailStr


class QuestionRequest(BaseModel):
    question: str
    task_id: str


class AggregationResult(BaseModel):
    count: int
    maximum: Optional[Union[float, int]]
    minimum: Optional[Union[float, int]]
    mean: Optional[Union[float, int]]
    total: Optional[Union[float, int]]
    max_user_details: Optional[List[dict]]
    min_user_details: Optional[List[dict]]


class AggregationResponse(BaseModel):
    task_id: str
    field: str
    output: AggregationResult


class AggregationRequest(BaseModel):
    task_id: str
    field: str
