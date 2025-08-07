import logging
import os
import ssl
from typing import Dict, Any

from celery import Celery
from celery.signals import after_setup_logger, after_setup_task_logger
from kombu import Exchange, Queue

from app.core.config import settings

logger = logging.getLogger(__name__)

celery_app = Celery(
    "coffee_shop",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_BACKEND_URL,
    broker_connection_retry_on_startup=True,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    worker_proc_alive_timeout=30,
    task_time_limit=30 * 60,
    task_soft_time_limit=25 * 60,
    result_expires=60 * 60 * 24 * 3,
    result_persistent=True,
    broker_connection_retry=True,
    broker_connection_max_retries=5,
    broker_transport_options={
        'max_retries': 3,
        'interval_start': 0,
        'interval_step': 0.2,
        'interval_max': 0.5,
    },
    security_key=os.getenv('CELERY_SECURITY_KEY'),
    security_certificate=os.getenv('CELERY_SECURITY_CERTIFICATE'),
    security_cert_store=os.getenv('CELERY_SECURITY_CERT_STORE'),
    task_queues=[
        Queue('default', Exchange('default'), routing_key='default'),
        Queue('cleanup', Exchange('cleanup'), routing_key='cleanup'),
        Queue('email', Exchange('email'), routing_key='email'),
    ],
    task_default_queue='default',
    task_default_exchange='default',
    task_default_routing_key='default',
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_track_started=True,
    worker_concurrency=4,
)

def route_task(name, args, kwargs, options, task=None, **kw):
    if name.startswith('app.tasks.cleanup'):
        return {'queue': 'cleanup'}
    if name.startswith('app.tasks.email'):
        return {'queue': 'email'}
    return None

celery_app.conf.task_routes = (route_task,)

def task_with_retry(self, *args, **kwargs):
    try:
        return self.run(*args, **kwargs)
    except Exception as exc:
        logger.error(f"Task {self.name} failed: {exc}")
        raise self.retry(exc=exc, countdown=60)

@after_setup_logger.connect
@after_setup_task_logger.connect
def setup_logger(logger, *args, **kwargs):
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    for handler in logger.handlers:
        handler.setFormatter(formatter)

celery_app.conf.worker_send_task_events = True
celery_app.conf.worker_hijack_root_logger = False
celery_app.conf.worker_redirect_stdouts = False
celery_app.conf.worker_redirect_stdouts_level = 'WARNING'
