from celery import Celery
from celery.signals import task_prerun, worker_process_init

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.request_id import generate_request_id, get_request_id, set_request_id

celery_app = Celery(
    "ai_photo_coach",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.analyze_photo"],
)

celery_app.conf.update(
    task_track_started=True,
    timezone="Asia/Shanghai",
    enable_utc=False,
    task_routes={
        "app.tasks.analyze_photo.run_analysis_task": {"queue": "analysis"},
    },
)


@worker_process_init.connect
def _init_worker_logging(**kwargs: object) -> None:
    """每个 worker 子进程启动时初始化日志系统。"""
    setup_logging(
        level=settings.log_level,
        env=settings.env,
        module_levels={"app.services": settings.log_level_services},
    )


@task_prerun.connect
def _inject_request_id(task_id: str, **kwargs: object) -> None:
    """任务执行前自动注入 request_id，确保全链路可追踪。

    若任务参数中已携带 request_id，则由任务内部自行覆盖；
    此处仅作为兜底，避免遗漏导致日志缺失 request_id。
    """
    current = get_request_id()
    if not current:
        set_request_id(f"task-{task_id[:12]}")

