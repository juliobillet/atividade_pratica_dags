from datetime import datetime
from airflow import DAG
import pandas as pd
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.operators.python import BranchPythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.postgres.operators.postgres import PostgresOperator


with DAG(
    dag_id="atividade_pratica",
    start_date=datetime(2020, 1, 1),
    schedule_interval=None,
    catchup=False
) as dag:

    def verify_returned_value(ti):
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
            "COPY (SELECT * FROM player) TO stdout WITH CSV HEADER",
            data_folder_path + "/players.csv"
        )


    def read_currency_db(ti):
        data_folder_path = ti.xcom_pull(task_ids="get_data_folder_path")
        pghook = PostgresHook(postgres_conn_id="pg_test")
        pghook.copy_expert(
            "COPY (SELECT * FROM currency) TO stdout WITH CSV HEADER",
            data_folder_path + "/currency.csv"
        )

    def read_players_ids_db(ti):
        data_folder_path = ti.xcom_pull(task_ids="get_data_folder_path")
        df = pd.read_csv(data_folder_path + "/players.csv")
        players_id_list = df["player_id"].tolist()
        ids = str(players_id_list).replace("[", "(").replace("]", ")")
        ti.xcom_push(key="player_ids", value=ids)
        print(ids)


    def update_currency_csv_file(ti):
        data_folder_path = ti.xcom_pull(task_ids="get_data_folder_path")
        pghook = PostgresHook(postgres_conn_id="pg_test")
        pghook.copy_expert(
            "COPY (SELECT * FROM currency) TO stdout WITH CSV HEADER",
            data_folder_path + "/updated_currency.csv"
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

    read_currency = PythonOperator(
        task_id="read_currency",
        python_callable=read_currency_db,
        provide_context=True
    )

    read_player_ids = PythonOperator(
        task_id="read_player_ids",
        python_callable=read_players_ids_db,
        provide_context=True
    )

    update_currency = PostgresOperator(
        task_id="update_currency",
        postgres_conn_id="pg_test",
        sql="UPDATE currency SET currency_amount = currency_amount * 2 WHERE player_id in"
            "{{ task_instance.xcom_pull(task_ids='read_player_ids', key='player_ids') }}"
    )

    update_currency_csv = PythonOperator(
        task_id="update_currency_csv",
        python_callable=update_currency_csv_file,
        provide_context=True
    )

    check_airflow_home >> decide_branch >> [create_data_folder, airflow_home_not_found]
    create_data_folder >> get_data_folder_path >> read_players >> read_currency >> read_player_ids >> update_currency >> update_currency_csv
