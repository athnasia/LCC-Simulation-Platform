"""Celery 任务入口。"""

from celery import Celery

from app.core.config import settings


celery_app = Celery(
	"lcc_app",
	broker=settings.CELERY_BROKER_URL,
	backend=settings.CELERY_RESULT_BACKEND,
	include=["app.worker.tasks"],
)

celery_app.conf.update(
	task_default_queue="lcc.default",
	task_serializer="json",
	accept_content=["json"],
	result_serializer="json",
	timezone="Asia/Shanghai",
	enable_utc=False,
	task_track_started=True,
)

celery_app.loader.import_default_modules()


@celery_app.task(name="app.tasks.ping")
def ping() -> str:
	"""用于验证 Worker 链路是否可用。"""
	return "pong"
