import pandas as pd
import re
from sqlalchemy import create_engine, text

from func_common import send_telegram_message, build_engine


def get_table_name(query: str) -> str | None:
    """
    Извлекает имя таблицы из простого SQL-запроса.
    Пример: "SELECT * FROM my_table WHERE id > 10" -> "my_table"
    """
    # Ищем первое вхождение ключевого слова FROM
    pattern = r'\bFROM\s+(["\']?[\w.]+["\']?)'
    match = re.search(pattern, query, re.IGNORECASE)
    return match.group(1) if match else None


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
        print(f"✅ Got {len(df)} rows, {len(df.columns)}")
        return df

    except Exception as e:
        msg = f'Function = get_df_from_db. Table = {get_table_name(query)}'
        send_telegram_message(message=msg)
        print(f"❌ Error: {e}")
        return pd.DataFrame()

    finally:
        engine.dispose()