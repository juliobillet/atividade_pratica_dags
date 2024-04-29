from datetime import datetime
from airflow import DAG
from airflow.operators.bash import BashOperator


with DAG(
    dag_id="ls_dag",
    start_date=datetime(2020, 1, 1),
    schedule_interval=None,
    catchup=False
) as dag:

    ls_task = BashOperator(
        task_id="ls_task",
        bash_command="ls -la $AIRFLOW_HOME"
    )

    ls_task
