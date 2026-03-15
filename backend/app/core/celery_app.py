from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "ai_finance",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.portfolio_tasks",
        "app.tasks.data_tasks",
        "app.tasks.model_tasks",
    ]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    beat_schedule={
        # Every day at 11 PM — fetch mutual fund NAV
        "fetch-nav-daily": {
            "task": "app.tasks.data_tasks.fetch_mutual_fund_nav",
            "schedule": 86400,
        },
        # Every hour — fetch and analyze news
        "fetch-news-hourly": {
            "task": "app.tasks.data_tasks.fetch_and_analyze_news",
            "schedule": 3600,
        },
        # Every day — check portfolio drift
        "check-portfolio-drift-daily": {
            "task": "app.tasks.portfolio_tasks.check_all_portfolio_drift",
            "schedule": 86400,
        },
        # Every week — retrain models
        "retrain-models-weekly": {
            "task": "app.tasks.model_tasks.retrain_all_models",
            "schedule": 604800,
        },
    }
)