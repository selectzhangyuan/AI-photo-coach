import logging
import time
import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.core.request_id import set_request_id
from app.models.analysis_feature import AnalysisFeature
from app.models.analysis_result import AnalysisResult
from app.models.analysis_task import AnalysisTask
from app.models.image_asset import ImageAsset
from app.services.composer.result_composer import get_result_composer
from app.services.cv.feature_extractor import get_feature_extractor
from app.services.llm.analyzer import get_llm_analyzer
from app.services.rules.edit_planner import get_edit_planner
from app.services.storage.s3_storage import get_storage_service

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.analyze_photo.run_analysis_task")
def run_analysis_task(task_id: str, request_id: str | None = None) -> None:
    # 恢复请求上下文（用于全链路追踪）
    set_request_id(request_id or task_id)

    db = SessionLocal()
    task_uuid = uuid.UUID(task_id)
    t_start = time.monotonic()

    try:
        task = db.get(AnalysisTask, task_uuid)
        if task is None:
            logger.warning("Task not found in database", extra={"task_id": task_id})
            return

        task.status = "RUNNING"
        task.started_at = datetime.now(timezone.utc)
        task.attempt_count += 1
        db.commit()

        logger.info(
            "Analysis task started",
            extra={
                "task_id": task_id,
                "image_id": str(task.image_id),
                "attempt_count": task.attempt_count,
            },
        )

        image = db.get(ImageAsset, task.image_id)
        if image is None:
            raise ValueError("Image not found")

        # ---- 1. 图片下载 ----
        t0 = time.monotonic()
        storage = get_storage_service()
        image_bytes = storage.download_bytes(image.object_key)
        logger.info(
            "Image downloaded",
            extra={
                "task_id": task_id,
                "object_key": image.object_key,
                "size_bytes": len(image_bytes),
                "duration_ms": round((time.monotonic() - t0) * 1000),
            },
        )

        feature_extractor = get_feature_extractor()
        llm_analyzer = get_llm_analyzer()
        edit_planner = get_edit_planner()
        result_composer = get_result_composer()

        # ---- 2. CV 特征提取 ----
        t0 = time.monotonic()
        feature_json = feature_extractor.extract(image_bytes=image_bytes, mime_type=image.mime_type)
        logger.info(
            "CV feature extraction completed",
            extra={
                "task_id": task_id,
                "duration_ms": round((time.monotonic() - t0) * 1000),
                "image_width": feature_json["image"]["width"],
                "image_height": feature_json["image"]["height"],
            },
        )

        existing_feature = db.execute(
            select(AnalysisFeature).where(AnalysisFeature.task_id == task.id)
        ).scalar_one_or_none()
        if existing_feature:
            existing_feature.feature_json = feature_json
            existing_feature.version = feature_json.get("version", "1.0")
            db.flush()
            feature_id = existing_feature.id
        else:
            feature = AnalysisFeature(
                task_id=task.id,
                image_id=task.image_id,
                version=feature_json.get("version", "1.0"),
                feature_json=feature_json,
            )
            db.add(feature)
            db.flush()
            feature_id = feature.id

        # ---- 3. LLM 分析 ----
        t0 = time.monotonic()
        llm_result = llm_analyzer.analyze(features=feature_json)
        logger.info(
            "LLM analysis completed",
            extra={
                "task_id": task_id,
                "model": task.model_name,
                "duration_ms": round((time.monotonic() - t0) * 1000),
                "suggestion_count": len(llm_result.get("suggestions", [])),
            },
        )

        # ---- 4. 规则生成 ----
        t0 = time.monotonic()
        edit_actions = edit_planner.plan(features=feature_json, suggestions=llm_result["suggestions"])
        logger.info(
            "Edit plan generated",
            extra={
                "task_id": task_id,
                "actions_count": len(edit_actions),
                "duration_ms": round((time.monotonic() - t0) * 1000),
            },
        )

        # ---- 5. 结果组装 ----
        t0 = time.monotonic()
        result_json = result_composer.compose(
            feature_id=str(feature_id),
            features=feature_json,
            llm_result=llm_result,
            edit_actions=edit_actions,
        )
        logger.info(
            "Result composed",
            extra={
                "task_id": task_id,
                "result_version": result_json.get("version"),
                "duration_ms": round((time.monotonic() - t0) * 1000),
            },
        )

        # ---- 6. 数据库写入 ----
        existing_result = db.execute(
            select(AnalysisResult).where(AnalysisResult.task_id == task.id)
        ).scalar_one_or_none()
        if existing_result:
            existing_result.result_json = result_json
            existing_result.version = result_json.get("version", "1.1")
        else:
            db.add(
                AnalysisResult(
                    task_id=task.id,
                    image_id=task.image_id,
                    version=result_json.get("version", "1.1"),
                    result_json=result_json,
                )
            )

        task.status = "SUCCEEDED"
        task.error_code = None
        task.error_message = None
        task.finished_at = datetime.now(timezone.utc)
        db.commit()

        total_ms = round((time.monotonic() - t_start) * 1000)
        logger.info(
            "Analysis task completed successfully",
            extra={
                "task_id": task_id,
                "total_duration_ms": total_ms,
            },
        )
    except Exception as exc:
        total_ms = round((time.monotonic() - t_start) * 1000)
        logger.exception(
            "Analysis task failed",
            extra={
                "task_id": task_id,
                "total_duration_ms": total_ms,
            },
        )
        db.rollback()
        failed_task = db.get(AnalysisTask, task_uuid)
        if failed_task:
            failed_task.status = "FAILED"
            failed_task.error_code = exc.__class__.__name__
            failed_task.error_message = str(exc)[:500]
            failed_task.finished_at = datetime.now(timezone.utc)
            db.commit()
    finally:
        db.close()
