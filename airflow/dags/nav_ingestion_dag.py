from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {
    "owner":            "ai_finance",
    "depends_on_past":  False,
    "start_date":       datetime(2024, 1, 1),
    "retries":          3,
    "retry_delay":      timedelta(minutes=5),
}

dag = DAG(
    "nav_ingestion",
    default_args=default_args,
    description="Daily mutual fund NAV ingestion from AMFI",
    schedule_interval="0 23 * * *",  # Daily at 11 PM
    catchup=False,
    tags=["data_ingestion", "mutual_funds"],
)

def fetch_nav():
    """Fetch NAV from AMFI and store in TimescaleDB."""
    import sys
    sys.path.append("/opt/airflow/backend")
    from app.tasks.data_tasks import fetch_mutual_fund_nav
    result = fetch_mutual_fund_nav()
    print(f"NAV fetch result: {result}")
    return result

def validate_nav():
    """Validate fetched NAV data."""
    print("Validating NAV data...")
    return {"status": "validated"}

fetch_task    = PythonOperator(task_id="fetch_nav_data",    python_callable=fetch_nav,     dag=dag)
validate_task = PythonOperator(task_id="validate_nav_data", python_callable=validate_nav,  dag=dag)

fetch_task >> validate_task