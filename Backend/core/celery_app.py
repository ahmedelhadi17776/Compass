from celery import Celery
from Backend.core.config import settings

# Create Celery instance
celery_app = Celery(
    "compass",
    backend=settings.CELERY_RESULT_BACKEND,
    broker=settings.CELERY_BROKER_URL,
    include=[
        "tasks.email_tasks",
        "tasks.workflow_tasks",
        "tasks.ai_tasks",
        "tasks.notification_tasks"
    ]
)

# Celery Configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_store_errors_even_if_ignored=True,
    task_send_sent_event=True,
    task_ignore_result=False,
    result_expires=3600,  # Results expire in 1 hour
    worker_max_tasks_per_child=1000,
    worker_prefetch_multiplier=1,
    task_routes={
        "tasks.email_tasks.*": {"queue": "email"},
        "tasks.workflow_tasks.*": {"queue": "workflow"},
        "tasks.ai_tasks.*": {"queue": "ai"},
        "tasks.notification_tasks.*": {"queue": "notification"}
    },
    task_default_priority=5,
    task_max_priority=10,
    task_create_missing_queues=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_store_eager_result=True,  # Store results even in eager mode
    task_eager_propagates=True,  # Propagate exceptions in eager mode
    # Use settings value for eager mode
    task_always_eager=settings.CELERY_TASK_ALWAYS_EAGER,
    result_backend_always_retry=True,  # Always retry backend operations
    result_backend_max_retries=10,  # Maximum number of retries for backend operations
    redis_backend_use_ssl=False,  # Disable SSL for Redis in test mode
    redis_max_connections=None,  # No connection limit in test mode
    broker_connection_retry=True,  # Retry broker connections
    broker_connection_max_retries=None  # Unlimited retries for broker connections
)

# Configure task routing
celery_app.conf.task_routes = {
    "tasks.email_tasks.*": {"queue": "email"},
    "tasks.workflow_tasks.*": {"queue": "workflow"},
    "tasks.ai_tasks.*": {"queue": "ai"},
    "tasks.notification_tasks.*": {"queue": "notification"}
}

# Configure task priorities
celery_app.conf.task_queue_max_priority = 10
celery_app.conf.task_default_priority = 5

# Configure task rate limits
celery_app.conf.task_annotations = {
    "tasks.email_tasks.send_email": {"rate_limit": "100/m"},
    "tasks.ai_tasks.*": {"rate_limit": "50/m"}
}
