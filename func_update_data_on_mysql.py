from sqlalchemy import text
import time

from func_common import send_telegram_message, build_engine


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
        analyze_tables: list = []
):
    engine = build_engine(db_user, db_password, db_host, db_port, db_dbname, read_timeout=300, write_timeout=300,
                          connect_timeout=300)

    with engine.connect() as conn:

        if analyze_tables != []:
            for tbl in analyze_tables:
                conn.execute(text("analyze table " + tbl))

        if big_query_flag:
            conn.execute(text("SET SQL_BIG_SELECTS=1"))
            conn.execute(text("SET MAX_JOIN_SIZE=18446744073709551615"))

        # conn = conn.execution_options(isolation_level="AUTOCOMMIT")
        if truncate == True: conn.exec_driver_sql(f"TRUNCATE TABLE {tbl_db}.{tbl_name}")
        conn.exec_driver_sql(query)
        conn.commit()


def mysql_update_view_with_retry(
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
        analyze_tables: list = [],
        max_retries: int = 5,
        retry_sleep_seconds: int = 30
):
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
                truncate = truncate,
                analyze_tables=analyze_tables
            )
            break
        except Exception as e:
            if attempt == max_retries:
                msg = f'Function = mysql_update_view_with_retry. Table = {tbl_db}.{tbl_name}. Script FAILED after {max_retries} tries.'
                send_telegram_message(message=msg)
                print(
                    f"Таблица {tbl_db}.{tbl_name} не обновлена после {max_retries} {'попыток' if max_retries > 1 else 'попытки'}")
                raise
            time.sleep(retry_sleep_seconds)