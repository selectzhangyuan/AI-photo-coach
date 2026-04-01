from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class CreateAnalysisTaskRequest(BaseModel):
    image_id: UUID


class CreateAnalysisTaskResponse(BaseModel):
    task_id: UUID
    task_type: str = "ANALYZE"
    status: str


class AnalysisTaskDetailResponse(BaseModel):
    task_id: UUID
    image_id: UUID
    task_type: str
    status: str
    model_name: str
    prompt_version: str
    attempt_count: int
    error_code: str | None = None
    error_message: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    result: dict[str, Any] | None = None


class AnalysisHistoryItem(BaseModel):
    task_id: UUID
    image_id: UUID
    task_type: str
    status: str
    created_at: datetime
    finished_at: datetime | None = None
    summary: str | None = None


class AnalysisHistoryResponse(BaseModel):
    items: list[AnalysisHistoryItem]


class RetryTaskResponse(BaseModel):
    task_id: UUID
    task_type: str = Field(default="ANALYZE")
    status: str = Field(default="PENDING")
