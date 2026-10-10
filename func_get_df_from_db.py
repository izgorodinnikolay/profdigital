import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import text

from func_common import log_errors, send_telegram_message, build_engine, get_table_name


load_dotenv('variables.env')

BOT_CHAT_ID_3 = os.getenv("BOT_CHAT_ID_3")
CHAT_3_TOPIC_PROCESS = os.getenv("CHAT_3_TOPIC_PROCESS")


def get_df_from_db(
        db_user: str,
        db_password: str,
        db_host: str,
        db_port: int,
        db_dbname: str,
        query: str,
        big_query_flag: bool = False,
        params: dict = None
) -> pd.DataFrame:
    engine = build_engine(db_user, db_password, db_host, db_port, db_dbname, read_timeout=300, write_timeout=300,
                          connect_timeout=300)

    try:

        with engine.connect() as conn:

            if big_query_flag:
                conn.execute(text("SET SQL_BIG_SELECTS=1"))
                conn.execute(text("SET MAX_JOIN_SIZE=18446744073709551615"))

            df = pd.read_sql(
                sql=text(query),
                con=conn,
                params=params
            )

        print(f"      ✅ Got {len(df)} rows, {len(df.columns)}")
        return df

    except Exception as e:
        msg = f'      Function = get_df_from_db. Table = {get_table_name(query)}'
        # print(msg)
        send_telegram_message(chat_id=BOT_CHAT_ID_3, message=msg, topic_id=CHAT_3_TOPIC_PROCESS)
        print(f"      ❌ Error: {e}")
        return pd.DataFrame()

    finally:
        engine.dispose()


@log_errors
def get_df_from_db_with_msg(
        db_user: str,
        db_password: str,
        db_host: str,
        db_port: int,
        db_dbname: str,
        query: str,
        df: str = 'no info',
        big_query_flag: bool = False,
        params: dict = None,
        notification_flg: bool = False
) -> pd.DataFrame:

    process_msg = f'upload data from ProfDigital in {df}'
    print(f'    {process_msg}')

    if notification_flg:
        send_telegram_message(chat_id=BOT_CHAT_ID_3, message=process_msg, topic_id=CHAT_3_TOPIC_PROCESS)

    # Исправлено: добавлен return и убраны ошибочные двоеточия типов данных
    return get_df_from_db(
        db_user=db_user,
        db_password=db_password,
        db_host=db_host,
        db_port=db_port,
        db_dbname=db_dbname,
        query=query,
        big_query_flag=big_query_flag,
        params=params
    )
