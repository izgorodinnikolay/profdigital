from sqlalchemy import create_engine, text


def mysql_update_view(
        db_user: str,
        db_password: str,
        db_host: str,
        db_port: int,
        db_dbname: str,
        tbl_name: str,
        tbl_db: str,
        query: str,
        big_query_flag: bool = False
):
    engine = create_engine(
        f'mysql+pymysql://{db_user}:{db_password}@{db_host}:{str(db_port)}/{db_dbname}'
    )

    with engine.connect() as conn:
        if big_query_flag:
            conn.execute(text("SET SQL_BIG_SELECTS=1"))
            conn.execute(text("SET MAX_JOIN_SIZE=18446744073709551615"))

        # conn = conn.execution_options(isolation_level="AUTOCOMMIT")
        conn.exec_driver_sql(f"TRUNCATE TABLE {tbl_db}.{tbl_name}")
        conn.exec_driver_sql(query)
        conn.commit()