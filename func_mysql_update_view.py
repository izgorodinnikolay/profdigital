import os
from sqlalchemy import text
from dotenv import load_dotenv
from time import sleep as sys_sleep

from func_common import log_errors, send_telegram_message, build_engine, read_sql_script, get_table_name

load_dotenv('variables.env')

BOT_CHAT_ID_3 = os.getenv("BOT_CHAT_ID_3")
CHAT_3_TOPIC_PROCESS = os.getenv("CHAT_3_TOPIC_PROCESS")


def mysql_update_view(
        db_user: str,
        db_password: str,
        db_host: str,
        db_port: int,
        db_dbname: str,
        tbl_name: str,
        tbl_db: str,
        query: str,
        big_query_flag: bool = False,
        truncate: bool = True,
        analyze_tables: set = set()
):
    engine = build_engine(db_user, db_password, db_host, db_port, db_dbname, read_timeout=300, write_timeout=300,
                          connect_timeout=300)

    with engine.connect() as conn:

        conn = conn.execution_options(isolation_level="AUTOCOMMIT")

        if analyze_tables != set():
            for tbl in analyze_tables:
                conn.execute(text("analyze table " + tbl))

        if big_query_flag:
            conn.execute(text("SET SQL_BIG_SELECTS=1"))
            conn.execute(text("SET MAX_JOIN_SIZE=18446744073709551615"))

        check_query = f"""SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = '{tbl_db}' AND TABLE_NAME = '{tbl_name}' LIMIT 1"""
        result = conn.exec_driver_sql(check_query).fetchone()

        if result:
            if truncate:
                conn.exec_driver_sql(f"TRUNCATE TABLE {tbl_db}.{tbl_name}")
            query = f"insert into {tbl_db}.{tbl_name}\n" + query
        else:
            query = f"create table {tbl_db}.{tbl_name} as\n" + query

        conn.exec_driver_sql(query)

    engine.dispose()


@log_errors
def mysql_update_view_with_retry(
        db_user: str,
        db_password: str,
        db_host: str,
        db_port: int,
        db_dbname: str,
        tbl_db: str,
        tbl_name: str,
        big_query_flag: bool = False,
        truncate: bool = True,
        max_retries: int = 5,
        retry_sleep_seconds: int = 30,
        notification_flg: bool = False
):
    process_msg = f'update data on ProfDigital {tbl_db}.{tbl_name}'
    print(f'    {process_msg}')

    if notification_flg:
        send_telegram_message(chat_id=BOT_CHAT_ID_3, message=process_msg, topic_id=CHAT_3_TOPIC_PROCESS)

    query = read_sql_script(f'{tbl_db}.{tbl_name}.sql')
    analyze_tables = get_table_name(query)

    for attempt in range(1, max_retries + 1):

        try:

            mysql_update_view(
                db_user=db_user,
                db_password=db_password,
                db_host=db_host,
                db_port=db_port,
                db_dbname=db_dbname,
                tbl_name=tbl_name,
                tbl_db=tbl_db,
                query=query,
                big_query_flag=big_query_flag,
                truncate=truncate,
                analyze_tables=analyze_tables
            )
            break

        except Exception as e:

            msg = f"Function MYSQL_UPDATE_VIEW FAILED to update table = {tbl_db}.{tbl_name}. Attempt={attempt}/{max_retries}."
            print(msg)

            if attempt == max_retries:
                msg = (
                    f"Function MYSQL_UPDATE_VIEW FAILED to update table = {tbl_db}.{tbl_name} after {max_retries} tries.\n"
                    f"Last error: {str(e)}"
                )

                send_telegram_message(chat_id=BOT_CHAT_ID_3, message=msg, topic_id=CHAT_3_TOPIC_PROCESS)
                raise RuntimeError(msg)

            sys_sleep(retry_sleep_seconds)