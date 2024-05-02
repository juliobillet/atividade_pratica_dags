from datetime import datetime
from airflow import DAG
import pandas as pd
import os
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.operators.python import BranchPythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.sensors.filesystem import FileSensor


with DAG(
    dag_id="atividade_pratica",
    start_date=datetime(2020, 1, 1),
    schedule_interval=None,
    catchup=False
) as dag:

    def verify_returned_value(**kwargs):
        ti = kwargs["ti"]
        returned_value = ti.xcom_pull(task_ids="check_airflow_home")

        if not str(returned_value).strip():
            return "airflow_home_not_found"
        elif str(returned_value).strip():
            return "create_data_folder"


    def airflow_home_error():
        print("An error occured while trying to obtain $AIRFLOW_HOME's value.")


    def read_players_db(ti):
        data_folder_path = ti.xcom_pull(task_ids="get_data_folder_path")
        pghook = PostgresHook(postgres_conn_id="pg_test")
        pghook.copy_expert(
            "COPY (SELECT * FROM players) TO stdout WITH CSV HEADER",
            data_folder_path + "/players.csv"
        )


    def read_currency_db(ti):
        data_folder_path = ti.xcom_pull(task_ids="get_airflow_home")
        pghook = PostgresHook(postgres_conn_id="pg_test")
        pghook.copy_expert(
            "COPY (SELECT * FROM currency) TO stdout WITH CSV HEADER",
            data_folder_path + "/currency.csv"
        )

    check_airflow_home = BashOperator(
        task_id="check_airflow_home",
        bash_command="echo $AIRFLOW_HOME",
        do_xcom_push=True
    )

    decide_branch = BranchPythonOperator(
        task_id="decide_branch",
        python_callable=verify_returned_value,
        provide_context=True
    )

    airflow_home_not_found = PythonOperator(
        task_id="airflow_home_not_found",
        python_callable=airflow_home_error
    )

    create_data_folder = BashOperator(
        task_id="create_data_folder",
        bash_command="mkdir -p $AIRFLOW_HOME/data"
    )

    get_data_folder_path = BashOperator(
        task_id="get_data_folder_path",
        bash_command="echo $AIRFLOW_HOME/data",
        do_xcom_push=True
    )

    read_players = PythonOperator(
        task_id="read_players",
        python_callable=read_players_db,
        provide_context=True
    )

    check_airflow_home >> decide_branch >> [create_data_folder, airflow_home_not_found]
    create_data_folder >> get_data_folder_path >> read_players
    # create_data_folder
    # airflow_home_found
    # airflow_home_not_found
