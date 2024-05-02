from airflow.operators.python import PythonOperator
from airflow.sensors.filesystem import FileSensor
from airflow import DAG
from datetime import datetime


with DAG(
    dag_id='check_file_dag',
    start_date=datetime(2020, 1, 1),
    schedule_interval=None,
    catchup=False
) as dag:

    file_path = '/home/ath/projects/atividade_pratica_dags/dags/ls_dag.py'

    file_sensor = FileSensor(
        task_id='check_file_existence',
        filepath=file_path,
        poke_interval=5,
        timeout=50,
    )


    def check_file_empty():
        with open(file_path, 'r') as file:
            content = file.read()
            if not content.strip():
                print(f'O arquivo {file_path} está vazio.')
            else:
                print(f'O arquivo {file_path} não está vazio.')


    check_file_task = PythonOperator(
        task_id='check_file_empty',
        python_callable=check_file_empty
    )

    file_sensor >> check_file_task
