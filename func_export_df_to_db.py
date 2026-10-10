import os
import pandas as pd
from dotenv import load_dotenv
from time import sleep as sys_sleep

from func_common import log_errors, send_telegram_message, build_engine


load_dotenv('variables.env')

MAX_RETRIES = int(os.getenv("MAX_RETRIES"))
RETRY_SLEEP_SECONDS = int(os.getenv("RETRY_SLEEP_SECONDS"))
BOT_CHAT_ID_3 = os.getenv("BOT_CHAT_ID_3")
CHAT_3_TOPIC_PROCESS = os.getenv("CHAT_3_TOPIC_PROCESS")


def export_df_to_db(
        df_src: pd.DataFrame,
        db_user: str,
        db_password: str,
        db_host: str,
        db_port: int,
        db_dbname: str,
        db_table: str,
        truncate: bool = True
):

    engine = build_engine(
        db_user, db_password, db_host, db_port, db_dbname,
        read_timeout=300, write_timeout=300, connect_timeout=300
    )

    with engine.connect() as conn:

        conn = conn.execution_options(isolation_level="AUTOCOMMIT")

        if truncate:

            check_query = f"""SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = '{db_dbname}' AND TABLE_NAME = '{db_table}' LIMIT 1"""
            result = conn.exec_driver_sql(check_query).fetchone()

            if result:
                conn.exec_driver_sql(f"TRUNCATE TABLE {db_dbname}.{db_table}")

        df_src.to_sql(
            name=db_table,
            con=conn,
            schema=db_dbname,
            if_exists='append',
            index=False,
            # chunksize=1000,
            # method='multi'
        )

    engine.dispose()


@log_errors
def export_df_to_db_with_retry(
        df_src: pd.DataFrame,
        db_user: str,
        db_password: str,
        db_host: str,
        db_port: int,
        db_dbname: str,
        db_table: str,
        truncate: bool = True,
        max_retries: int = MAX_RETRIES,
        retry_sleep_seconds: int = RETRY_SLEEP_SECONDS,
        notification_flg: bool = False
):
    process_msg = f'load data to ProfDigital {db_dbname}.{db_table}'
    print(f'  {process_msg}')

    if notification_flg:
        send_telegram_message(chat_id=BOT_CHAT_ID_3, message=process_msg, topic_id=CHAT_3_TOPIC_PROCESS)

    for attempt in range(1, max_retries + 1):
        try:
            export_df_to_db(
                df_src=df_src,
                db_user=db_user,
                db_password=db_password,
                db_host=db_host,
                db_port=db_port,
                db_dbname=db_dbname,
                db_table=db_table,
                truncate=truncate
            )
            return True

        except Exception as e:

            msg = f"Function EXPORT_DF_TO_DB FAILED to upload table {db_dbname}.{db_table}. Attempt={attempt}/{max_retries}."
            print(msg)

            if attempt == max_retries:
                msg = (
                    f"Function EXPORT_DF_TO_DB FAILED to upload table {db_dbname}.{db_table} after {max_retries} tries.\n"
                    f"Last error: {str(e)}"
                )

                send_telegram_message(chat_id=BOT_CHAT_ID_3, message=msg, topic_id=CHAT_3_TOPIC_PROCESS)
                raise RuntimeError(msg)

            sys_sleep(retry_sleep_seconds)