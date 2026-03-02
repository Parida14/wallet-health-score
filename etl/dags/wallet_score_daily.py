"""Airflow DAG scheduling the wallet health ETL pipeline."""

from __future__ import annotations

import json
from datetime import datetime, timedelta

from airflow import DAG
from airflow.models import Variable
from airflow.operators.python import PythonOperator

from wallet_etl.pipeline.daily_job import run_wallet_pipeline

DEFAULT_ADDRESSES_VAR = "WALLET_PIPELINE_ADDRESSES"
DEFAULT_WALLET_ADDRESSES = ["0xd8da6bf26964af9d7eed9e03e53415d37aa96045"]


def _load_addresses(**_context) -> list[str]:
    stored = Variable.get(
        DEFAULT_ADDRESSES_VAR, default_var=json.dumps(DEFAULT_WALLET_ADDRESSES)
    )
    return json.loads(stored)


def _run_pipeline(**context) -> None:
    addresses = context["ti"].xcom_pull(task_ids="load_addresses")
    if not addresses:
        raise ValueError(
            "No wallet addresses configured for the pipeline. "
            f"Set Airflow Variable '{DEFAULT_ADDRESSES_VAR}' to a JSON list."
        )
    run_wallet_pipeline(addresses)


with DAG(
    dag_id="wallet_health_daily",
    description="Daily refresh of wallet scores and features.",
    default_args={
        "owner": "data-eng",
        "depends_on_past": False,
        "retries": 1,
        "retry_delay": timedelta(minutes=10),
    },
    schedule_interval="0 6 * * *",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["wallet-health", "mvp"],
) as dag:
    load_addresses = PythonOperator(task_id="load_addresses", python_callable=_load_addresses)

    run_pipeline_task = PythonOperator(task_id="run_pipeline", python_callable=_run_pipeline)

    load_addresses >> run_pipeline_task
