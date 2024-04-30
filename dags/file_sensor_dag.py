from airflow.sensors.filesystem import FileSensor
from airflow import DAG
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2024, 4, 30),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG('check_file_dag', default_args=default_args, schedule_interval='@once')

file_path = '/caminho/para/seu/arquivo.txt'

file_sensor = FileSensor(
    task_id='check_file_existence',
    filepath=file_path,
    poke_interval=60,  # Intervalo de verificação em segundos
    timeout=600,  # Tempo máximo de espera em segundos
    dag=dag,
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
    python_callable=check_file_empty,
    dag=dag,
)

file_sensor >> check_file_task
