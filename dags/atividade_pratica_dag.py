from datetime import datetime
from airflow import DAG
import pandas as pd
import os
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.operators.python import BranchPythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.postgres.operators.postgres import PostgresOperator


with (DAG(
    dag_id="atividade_pratica_dag",
    start_date=datetime(2020, 1, 1),
    schedule_interval=None,
    catchup=False
) as dag):
    def share_path(ti):
        with open("/data/path.txt", "r") as data:
            path = data.read()
        ti.xcom_push(key="path", value=path)
    
    
    def read_players(ti):
        airflow_home = ti.xcom_pull(task_ids="share_path_task", key="path")
        pghook = PostgresHook(postgres_conn_id="PG_SWORDBLAST")
        pghook.copy_expert(
            "COPY (SELECT * FROM players) TO stdout WITH CSV HEADER",
            airflow_home + "/data/players.csv"
        )


    def read_currency(ti):
        airflow_home = ti.xcom_pull(task_ids="share_path_task", key="path")
        pghook = PostgresHook(postgres_conn_id="PG_SWORDBLAST")
        pghook.copy_expert(
            "COPY (SELECT * FROM currency) TO stdout WITH CSV HEADER",
            airflow_home + "/data/currency.csv"
        )


    def update_currency_csv(ti):
        airflow_home = ti.xcom_pull(task_ids="share_path_task", key="path")
        pghook = PostgresHook(postgres_conn_id="PG_SWORDBLAST")
        pghook.copy_expert(
            "COPY (SELECT * FROM currency) TO stdout WITH CSV HEADER",
            airflow_home + "/data/currency_updated.csv"
        )


    def read_player_ids(ti):
        airflow_home = ti.xcom_pull(task_ids="share_path_task", key="path")
        df = pd.read_csv(airflow_home + "/data/players.csv")
        player_id_list = df["player_id"].tolist()
        ids = str(player_id_list).replace("[", "(").replace("]", ")")
        ti.xcom_push(key="player_ids", value=ids)


    def path_exists(ti):
        file_path = ti.xcom_pull(task_ids="share_path_task", key="path") + "/data/path.txt"
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            return "path_exists"
        else:
            return "path_does_not_exist"


    def print_message(caller):
        if caller == "path_exists":
            print("Caminho de AIRFLOW_HOME encontrado, prosseguindo para a próxima task...")
        else:
            print("Ocorreu um erro ao tentar recuperar o caminho da variável de ambiente AIRFLOW_HOME")


    create_data_folder_task = BashOperator(
        task_id="create_data_folder",
        bash_command="mkdir -p $AIRFLOW_HOME/data"
    )

    get_path_task = BashOperator(
        task_id="get_path",
        bash_command="echo $AIRFLOW_HOME  > $AIRFLOW_HOME/data/path.txt"
    )

    decide_branch_task = BranchPythonOperator(
        task_id="decide_branch",
        python_callable=path_exists
    )
    
    path_exists_task = PythonOperator(
        task_id="path_exists",
        python_callable=print_message,
        op_kwargs={"caller": "path_exists"}
    )

    share_path_task = PythonOperator(
        task_id="share_path",
        python_callable=share_path
    )

    path_does_not_exist_task = PythonOperator(
        task_id="path_does_not_exist",
        python_callable=print_message,
        op_kwargs={"caller": None}
    )

    read_players_task = PythonOperator(
        task_id="read_players",
        python_callable=read_players
    )

    read_currency_task = PythonOperator(
        task_id="read_currency",
        python_callable=read_currency
    )

    read_player_ids_task = PythonOperator(
        task_id="read_player_ids",
        python_callable=read_player_ids
    )

    update_currency_task = PostgresOperator(
        task_id="update_currency",
        postgres_conn_id="PG_SWORDBLAST",
        sql="UPDATE currency SET currency_amount = currency_amount * 2 WHERE player_id in"
            "{{ task_instance.xcom_pull(task_ids='read_player_ids', key='player_ids') }}"
    )

    update_currency_csv_task = PythonOperator(
        task_id="update_currency_csv",
        python_callable=update_currency_csv
    )

    create_data_folder_task >> get_path_task >> decide_branch_task >> [path_exists_task, path_does_not_exist_task]
    path_exists_task >> share_path_task >> read_players_task >> read_currency_task >> read_player_ids_task >> update_currency_task >> update_currency_csv_task
