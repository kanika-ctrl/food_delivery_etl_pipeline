import sys
from pathlib import Path
from pendulum import datetime
from datetime import timedelta

sys.path.append(str(Path(__file__).resolve().parent.parent))

from airflow.sdk import dag, task
from ingestion import fetch_data
from transformation import json_to_csv
from transformation import feature_engineering


POSTGRES_Conn_ID = "postgres_default"

# DAG Definition
@dag(
    dag_id='food_delivery_etl_pipeline',
    start_date=datetime(2026, 1, 30),
    schedule="@daily",
    default_args={
        "owner": "airflow",
        "retries": 2,
        "retry_delay": timedelta(minutes=5)
    },
    catchup=False,
    description='ETL pipeline for food delivery restaurant data',
    tags=['food-delivery', 'etl', 'restaurant-data']
)
def food_delivery_pipeline():
    @task
    def fetch_data_task():
        fetch_data.fetch_data()
        return "Data Fetched Completely"
    
    @task
    def json_to_csv_task():
        try:
            json_to_csv.json_to_csv()
            return "converted json to csv"
        except Exception as e:
            return f"Error occurred:{e}"

    @task
    def transform_data_task():
        try:
            feature_engineering.transform_data()
            return "transformed data completed"
        except Exception as e:
            return f"Error occurred:{e}"
    
    # Task dependencies and return
    fetch_data_task() >> json_to_csv_task() >> transform_data_task()


# Instantiate the DAG
food_etl_dag = food_delivery_pipeline()
