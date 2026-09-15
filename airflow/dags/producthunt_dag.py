from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    "owner": "vishal",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="producthunt_pipeline",
    default_args=default_args,
    description="Pull Product Hunt data, load to Snowflake, transform with dbt",
    schedule="@hourly",
    start_date=datetime(2026, 9, 14),
    catchup=False,
    tags=["portfolio", "producthunt"],
) as dag:

    run_ingestion = BashOperator(
        task_id="run_ingestion_script",
        bash_command="cd /opt/airflow/producthunt_project && python /opt/airflow/producthunt_project/load_to_snowflake.py",
    )

    run_dbt = BashOperator(
        task_id="run_dbt_transform",
        bash_command="cd /opt/airflow/producthunt_project/producthunt_dbt && dbt run --profiles-dir /opt/airflow/producthunt_project/dbt_profiles",
    )

    run_ingestion >> run_dbt
