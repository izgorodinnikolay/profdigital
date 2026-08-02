import pandas as pd
import requests
import os
import sys
import time
from datetime import datetime, time, timezone
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth
from sqlalchemy import create_engine, text

load_dotenv(r'C:\Users\user\Desktop\Maks\projects\invoices_2026_07_26\variables.env')

ERROR_LOG_FILE = os.getenv("ERROR_LOG_FILE")

def write_error_to_txt(text: str, file_name: str = ERROR_LOG_FILE):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(file_name, 'a', encoding='utf-8') as f:
        f.write(f'[{timestamp}] {text}\n')


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
    engine = create_engine(
        f'mysql+pymysql://{db_user}:{db_password}@{db_host}:{str(db_port)}/{db_dbname}'
    )

    with engine.connect() as conn:
        conn = conn.execution_options(isolation_level="AUTOCOMMIT")
        if truncate:
            conn.exec_driver_sql(f"TRUNCATE TABLE {db_dbname}.{db_table}")
        df_src.to_sql(
            name=db_table,
            con=engine,
            schema=db_dbname,
            if_exists='append',
            index=False,
            # chunksize=1000,
            # method='multi'
        )


def export_df_to_db_with_retry(
        df_src: pd.DataFrame,
        db_user: str,
        db_password: str,
        db_host: str,
        db_port: int,
        db_dbname: str,
        db_table: str,
        truncate: bool = True,
        max_retries: int = 10,
        retry_sleep_seconds: int = 300
):
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
            write_error_to_txt(
                f'export_df_to_db error. table={db_table}. attempt={attempt}/{max_retries}. error={str(e)}'
            )

            if attempt >= max_retries:
                write_error_to_txt(f'script finished after {max_retries} tries')
                sys.exit(1)

            time.sleep(retry_sleep_seconds)

    return False


def build_status_df(
        document: str,
        status: str,
        error_type=None,
        error_text=None,
        error_response_text=None
) -> pd.DataFrame:
    return pd.DataFrame([{
        'document': document,
        'status_dttm': datetime.now(timezone.utc),
        'status': status,
        'error_type': error_type,
        'error_text': error_text,
        'error_response_text': error_response_text[:500] if isinstance(error_response_text,
                                                                       str) else error_response_text
    }])


def update_column_type(df_in: pd.DataFrame, column_name: str, column_type: str):
    if column_type == 'datetime':
        return df_in[column_name].replace(['0', 0, '0000-00-00', '0000-00-00 00:00:00', ''], pd.NA).apply(
            pd.to_datetime, utc=True, errors='coerce')
    elif column_type in ['string', 'boolean', 'int', 'float']:
        return df_in[column_name].astype(column_type)
    else:
        return df_in[column_name]


def get_1с_data(
        scloud_base: str,
        scloud_user: str,
        scloud_password: str,
        document: str,
        dict_columns: dict = {},
        explode_column: str = '',
        dict_explode_columns: dict = {},
        dttm_from_export: str = ''
):
    url = f'{scloud_base}/{document}'
    headers = {'Accept': 'application/json'}
    response = None
    params = dict()
    params['$format'] = 'json'
    if dict_columns != {}: params['$select'] = ','.join(dict_columns.keys())
    if dttm_from_export != '': params['$filter'] = f"Date gt datetime'{dttm_from_export}'"

    try:
        response = requests.get(
            url=url,
            headers=headers,
            params=params,
            auth=HTTPBasicAuth(scloud_user, scloud_password),
            timeout=30
        )

        response.raise_for_status()

        data = response.json()
        source_for_df = data.get('value', data)
        df = pd.DataFrame(source_for_df)

        if len(dict_columns) > 0:
            df = df.rename(
                columns={key: value[0] for key, value in dict_columns.items()}
            )[[value[0] for value in dict_columns.values()]]

            for value in dict_columns.values():
                df[value[0]] = update_column_type(
                    df_in=df,
                    column_name=value[0],
                    column_type=value[1]
                )

        if explode_column != '':
            df_exploded = df.explode(explode_column, ignore_index=True)
            df_normalized = pd.json_normalize(df_exploded[explode_column])

            if len(dict_explode_columns) > 0:
                df_normalized = df_normalized.rename(
                    columns={key: value[0] for key, value in dict_explode_columns.items()}
                )[[value[0] for value in dict_explode_columns.values()]]

                for value in dict_explode_columns.values():
                    df_normalized[value[0]] = update_column_type(
                        df_in=df_normalized,
                        column_name=value[0],
                        column_type=value[1]
                    )

            ref_col = dict_columns['Ref_Key'][0] if 'Ref_Key' in dict_columns else 'Ref_Key'
            df_exploded = pd.concat([df_exploded[[ref_col]], df_normalized], axis=1)
            df = df.drop(columns=explode_column)

            return df, df_exploded, pd.DataFrame()

        return df, pd.DataFrame(), pd.DataFrame()

    except requests.exceptions.HTTPError as e:
        response_text = response.text[:500] if response is not None else ''
        status_df = build_status_df(
            document=document,
            status='failure',
            error_type='HTTP',
            error_text=str(e),
            error_response_text=response_text
        )
        return pd.DataFrame(), pd.DataFrame(), status_df

    except requests.exceptions.ConnectionError as e:
        response_text = response.text[:500] if response is not None else None
        status_df = build_status_df(
            document=document,
            status='failure',
            error_type='Connection',
            error_text=str(e),
            error_response_text=response_text
        )
        return pd.DataFrame(), pd.DataFrame(), status_df

    except ValueError as e:
        response_text = response.text[:500] if response is not None else None
        status_df = build_status_df(
            document=document,
            status='failure',
            error_type='JSON',
            error_text=str(e),
            error_response_text=response_text
        )
        return pd.DataFrame(), pd.DataFrame(), status_df

    except Exception as e:
        response_text = response.text[:500] if response is not None else None
        status_df = build_status_df(
            document=document,
            status='failure',
            error_type='other',
            error_text=str(e),
            error_response_text=response_text
        )
        return pd.DataFrame(), pd.DataFrame(), status_df


def get_1с_data_with_retry(
        scloud_base: str,
        scloud_user: str,
        scloud_password: str,
        document: str,
        status_db_user: str,
        status_db_password: str,
        status_db_host: str,
        status_db_port: int,
        status_db_dbname: str,
        status_db_table: str = 'status_1c',
        dict_columns: dict = {},
        explode_column: str = '',
        dict_explode_columns: dict = {},
        dttm_from_export: str = '',
        max_retries: int = 10,
        retry_sleep_seconds: int = 300
):
    for attempt in range(1, max_retries + 1):

        df, df_exploded, status_df = get_1с_data(
            scloud_base=scloud_base,
            scloud_user=scloud_user,
            scloud_password=scloud_password,
            document=document,
            dict_columns=dict_columns,
            explode_column=explode_column,
            dict_explode_columns=dict_explode_columns,
            dttm_from_export=dttm_from_export
        )

        if status_df.empty:
            success_status_df = build_status_df(
                document=document,
                status='success',
                error_type=None,
                error_text=None,
                error_response_text=None
            )

            export_df_to_db_with_retry(
                df_src=success_status_df,
                db_user=status_db_user,
                db_password=status_db_password,
                db_host=status_db_host,
                db_port=status_db_port,
                db_dbname=status_db_dbname,
                db_table=status_db_table,
                truncate=False,
                max_retries=max_retries,
                retry_sleep_seconds=retry_sleep_seconds
            )

            return df, df_exploded

        export_df_to_db_with_retry(
            df_src=status_df,
            db_user=status_db_user,
            db_password=status_db_password,
            db_host=status_db_host,
            db_port=status_db_port,
            db_dbname=status_db_dbname,
            db_table=status_db_table,
            truncate=False,
            max_retries=max_retries,
            retry_sleep_seconds=retry_sleep_seconds
        )

        write_error_to_txt(
            f'get_1с_data error. document={document}. '
            f'attempt={attempt}/{max_retries}. '
            f'error_type={status_df.iloc[0]["error_type"]}. '
            f'error_text={status_df.iloc[0]["error_text"]}'
        )

        if attempt >= max_retries:
            write_error_to_txt(f'get_1с_data error. document={document}. Script finished after 10 tries.')
            sys.exit(1)

        time.sleep(retry_sleep_seconds)

    return pd.DataFrame(), pd.DataFrame()


def nomenclature_text_gr(nomenclature_text: str) -> str:
    if 'SMM' in nomenclature_text:
        return 'SMM'
    elif nomenclature_text == 'Автообзвон':
        return 'Автообзвон'
    elif 'Агентские услуги' in nomenclature_text or 'Агентское вознаграждение' in nomenclature_text:
        return 'Агентские услуги'
    elif 'абинета ВК' in nomenclature_text:
        return 'ВК'
    elif 'нтеграц' in nomenclature_text or 'Подключение к агрегатору' in nomenclature_text:
        return 'Интеграця'
    elif 'Контекст' in nomenclature_text:
        return 'Контекстная реклама'
    elif 'Оплата стоимости лидов' in nomenclature_text or 'Флоктори' in nomenclature_text or 'RIS PROMO' in nomenclature_text:
        return 'Лиды'
    elif 'Лендинг' in nomenclature_text or 'лендинг' in nomenclature_text:
        return 'Лендинг'
    elif 'Маркетинговые услуги' in nomenclature_text:
        return 'Маркетинговые услуги'
    elif 'Посев' in nomenclature_text:
        return 'Посевы'
    elif 'Таргет' in nomenclature_text or 'Пополнение бюджета' in nomenclature_text:
        return 'Таргет'
    elif 'Ведение страницы' in nomenclature_text or 'сайт' in nomenclature_text:
        return 'Сайт'
    elif 'трафик' in nomenclature_text:
        return 'Трафик'
    elif 'Услуги предикторов' in nomenclature_text:
        'Услуги предикторов'
    elif 'Разработка чат-бота' in nomenclature_text:
        return 'Чат бот'
    elif 'Тест' in nomenclature_text:
        return 'Тест'
    else:
        return 'Прочее'