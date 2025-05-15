from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from airflow_tasks.download import download_from_drive
from airflow_tasks.preprocess import preprocess_data
from airflow_tasks.evaluate import evaluate_quality
from airflow_tasks.save import save_clean_data

default_args = {
    'start_date': datetime(2024, 1, 1),
    'retries': 1
}

with DAG(
    dag_id='sudanese_dialect_data_pipeline',
    default_args=default_args,
    schedule_interval=None,
    catchup=False
) as dag:

    download = PythonOperator(
        task_id='download_dataset',
        python_callable=download_from_drive
    )

    preprocess = PythonOperator(
        task_id='preprocess_dataset',
        python_callable=preprocess_data
    )

    evaluate = PythonOperator(
        task_id='evaluate_quality',
        python_callable=evaluate_quality
    )

    save = PythonOperator(
        task_id='save_clean_data',
        python_callable=save_clean_data
    )

    download >> preprocess >> evaluate >> save
