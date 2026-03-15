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
        # Every 5 minutes — market summary
        "fetch-market-summary": {
            "task":     "app.tasks.data_tasks.fetch_market_summary",
            "schedule": 300,
        },
        # Every 15 minutes — stock prices
        "fetch-stock-prices": {
            "task":     "app.tasks.data_tasks.fetch_stock_prices",
            "schedule": 900,
        },
        # Daily at 11 PM — NAV data
        "fetch-nav-daily": {
            "task":     "app.tasks.data_tasks.fetch_mutual_fund_nav",
            "schedule": 86400,
        },
        # Hourly — news analysis
        "fetch-news-hourly": {
            "task":     "app.tasks.data_tasks.fetch_and_analyze_news",
            "schedule": 3600,
        },
        # Daily — NIFTY history
        "update-nifty-history": {
            "task":     "app.tasks.data_tasks.update_nifty_history",
            "schedule": 86400,
        },
        # Weekly — macro data
        "fetch-macro-weekly": {
            "task":     "app.tasks.data_tasks.fetch_macro_data",
            "schedule": 604800,
        },
        # Daily — portfolio drift check
        "check-portfolio-drift-daily": {
            "task":     "app.tasks.portfolio_tasks.check_all_portfolio_drift",
            "schedule": 86400,
        },
        # Weekly — model retrain
        "retrain-models-weekly": {
            "task":     "app.tasks.model_tasks.retrain_all_models",
            "schedule": 604800,
        },
    }
)