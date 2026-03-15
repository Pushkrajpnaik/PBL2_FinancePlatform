from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {
    "owner":           "ai_finance",
    "depends_on_past": False,
    "start_date":      datetime(2024, 1, 1),
    "retries":         2,
    "retry_delay":     timedelta(minutes=2),
}

dag = DAG(
    "news_nlp_pipeline",
    default_args=default_args,
    description="Hourly news fetching and sentiment analysis",
    schedule_interval="0 * * * *",  # Every hour
    catchup=False,
    tags=["nlp", "news", "sentiment"],
)

def fetch_news():
    print("Fetching financial news from RSS feeds...")
    return {"articles_fetched": 8}

def run_sentiment():
    print("Running FinBERT sentiment analysis...")
    return {"articles_analyzed": 8}

def store_results():
    print("Storing sentiment results to MongoDB...")
    return {"status": "stored"}

def generate_alerts():
    print("Generating risk alerts...")
    return {"alerts_generated": 2}

t1 = PythonOperator(task_id="fetch_news",        python_callable=fetch_news,     dag=dag)
t2 = PythonOperator(task_id="run_sentiment",     python_callable=run_sentiment,  dag=dag)
t3 = PythonOperator(task_id="store_results",     python_callable=store_results,  dag=dag)
t4 = PythonOperator(task_id="generate_alerts",   python_callable=generate_alerts,dag=dag)

t1 >> t2 >> t3 >> t4