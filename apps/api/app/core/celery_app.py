from celery import Celery

from app.core.config import settings

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

