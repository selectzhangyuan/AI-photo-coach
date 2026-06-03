import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.request_id import get_request_id
from app.deps import get_current_user_id
from app.models.analysis_result import AnalysisResult
from app.models.analysis_task import AnalysisTask
from app.models.image_asset import ImageAsset
from app.schemas.analysis import (
    AnalysisHistoryItem,
    AnalysisHistoryResponse,
    AnalysisTaskDetailResponse,
    CreateAnalysisTaskRequest,
    CreateAnalysisTaskResponse,
    RetryTaskResponse,
)
from app.tasks.analyze_photo import run_analysis_task

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analysis", tags=["analysis"])


def _build_detail_response(task: AnalysisTask, result: dict[str, Any] | None) -> AnalysisTaskDetailResponse:
    return AnalysisTaskDetailResponse(
        task_id=task.id,
        image_id=task.image_id,
        task_type=task.task_type,
        status=task.status,
        model_name=task.model_name,
        prompt_version=task.prompt_version,
        attempt_count=task.attempt_count,
        error_code=task.error_code,
        error_message=task.error_message,
        created_at=task.created_at,
        started_at=task.started_at,
        finished_at=task.finished_at,
        result=result,
    )


@router.post("/tasks", response_model=CreateAnalysisTaskResponse)
def create_task(
    payload: CreateAnalysisTaskRequest,
    db: Session = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> CreateAnalysisTaskResponse:

    image = db.get(ImageAsset, payload.image_id)
    if image is None:
        raise HTTPException(status_code=404, detail="Image not found")
    if image.user_id != user_id:
        raise HTTPException(status_code=403, detail="No permission for this image")

    task = AnalysisTask(
        user_id=user_id,
        image_id=image.id,
        task_type="ANALYZE",
        status="PENDING",
        model_name=settings.model_name,
        prompt_version=settings.prompt_version,
        attempt_count=0,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    request_id = get_request_id()
    logger.info(
        "Analysis task created",
        extra={"task_id": str(task.id), "image_id": str(image.id), "user_id": str(user_id)},
    )

    run_analysis_task.delay(str(task.id), request_id=request_id)

    return CreateAnalysisTaskResponse(task_id=task.id, task_type=task.task_type, status=task.status)


@router.get("/tasks/{task_id}", response_model=AnalysisTaskDetailResponse)
def get_task_detail(
    task_id: uuid.UUID,
    db: Session = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> AnalysisTaskDetailResponse:
    task = db.get(AnalysisTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.user_id != user_id:
        raise HTTPException(status_code=403, detail="No permission for this task")

    result = db.execute(select(AnalysisResult).where(AnalysisResult.task_id == task.id)).scalar_one_or_none()
    return _build_detail_response(task, result.result_json if result else None)


@router.get("/history", response_model=AnalysisHistoryResponse)
def get_history(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> AnalysisHistoryResponse:

    tasks = db.execute(
        select(AnalysisTask)
        .where(AnalysisTask.user_id == user_id)
        .order_by(desc(AnalysisTask.created_at))
        .limit(limit)
    ).scalars()

    items: list[AnalysisHistoryItem] = []
    for task in tasks:
        result = db.execute(select(AnalysisResult).where(AnalysisResult.task_id == task.id)).scalar_one_or_none()
        summary = None
        if result and isinstance(result.result_json, dict):
            summary = result.result_json.get("summary")

        items.append(
            AnalysisHistoryItem(
                task_id=task.id,
                image_id=task.image_id,
                task_type=task.task_type,
                status=task.status,
                created_at=task.created_at,
                finished_at=task.finished_at,
                summary=summary,
            )
        )

    return AnalysisHistoryResponse(items=items)


@router.post("/tasks/{task_id}/retry", response_model=RetryTaskResponse)
def retry_task(
    task_id: uuid.UUID,
    db: Session = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> RetryTaskResponse:
    task = db.get(AnalysisTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.user_id != user_id:
        raise HTTPException(status_code=403, detail="No permission for this task")
    if task.status not in {"FAILED", "SUCCEEDED"}:
        raise HTTPException(status_code=400, detail="Task is still running")

    task.status = "PENDING"
    task.error_code = None
    task.error_message = None
    task.started_at = None
    task.finished_at = None
    db.commit()

    request_id = get_request_id()
    logger.info(
        "Analysis task retried",
        extra={"task_id": str(task.id), "user_id": str(user_id)},
    )

    run_analysis_task.delay(str(task.id), request_id=request_id)
    return RetryTaskResponse(task_id=task.id, task_type=task.task_type, status=task.status)
