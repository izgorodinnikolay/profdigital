import pandas as pd
from sqlalchemy import create_engine, text


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
    engine = create_engine(
        f'mysql+pymysql://{db_user}:{db_password}@{db_host}:{str(db_port)}/{db_dbname}'
    )

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
        print(f"❌ Error: {e}")
        return pd.DataFrame()

    finally:
        engine.dispose()