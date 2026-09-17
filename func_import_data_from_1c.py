import pandas as pd
import requests
import os
import sys
from datetime import datetime, timezone
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth
from sqlalchemy import text
from time import sleep
from typing import Dict, List, Tuple, Optional, Any

from func_common import send_telegram_message, build_engine

load_dotenv(r'C:\Users\user\Desktop\Maks\projects\invoices_2026_07_26\variables.env')

MAX_RETRIES = int(os.getenv("MAX_RETRIES"))
RETRY_SLEEP_SECONDS = int(os.getenv("RETRY_SLEEP_SECONDS"))
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
    engine = build_engine(db_user, db_password, db_host, db_port, db_dbname, read_timeout=300, write_timeout=300,
                          connect_timeout=300)

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
        max_retries: int = MAX_RETRIES,
        retry_sleep_seconds: int = RETRY_SLEEP_SECONDS
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
                msg = f'Function = export_df_to_db_with_retry. Table = {db_dbname}.{db_table} . Script FAILED after {MAX_RETRIES} tries.'
                send_telegram_message(message=msg)
                write_error_to_txt(f'script finished after {max_retries} tries')
                sys.exit(1)

            sleep(retry_sleep_seconds)

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


def _build_failure_status_df(document, exception, response=None):
    if isinstance(exception, requests.exceptions.HTTPError):
        error_type = 'HTTP'
    elif isinstance(exception, requests.exceptions.ConnectionError):
        error_type = 'Connection'
    elif isinstance(exception, ValueError):
        error_type = 'JSON'
    else:
        error_type = 'Other'

    error_response_text = response.text[:500] if response is not None else ''

    return build_status_df(
        document=document,
        status='failure',
        error_type=error_type,
        error_text=str(exception),
        error_response_text=error_response_text
    )


def update_column_type(df_in: pd.DataFrame, column_name: str, column_type: str):
    if column_type == 'datetime':
        return df_in[column_name].replace(['0', 0, '0000-00-00', '0000-00-00 00:00:00', ''], pd.NA).apply(
            pd.to_datetime, utc=True, errors='coerce')
    elif column_type in ['int', 'float']:
        return df_in[column_name].fillna(0).astype(column_type)
    elif column_type in ['string', 'boolean']:
        return df_in[column_name].astype(column_type)
    else:
        return df_in[column_name]


def get_1с_data(
        scloud_base: str,
        scloud_user: str,
        scloud_password: str,
        document: str,
        dict_columns: Optional[Dict[str, List[Any]]] = None,
        explode_column: str = '',
        dict_explode_columns: Optional[Dict[str, List[Any]]] = None,
        dttm_from_export: str = ''
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Получает данные из API 1С, нормализует и возвращает:
    - основной DataFrame,
    - exploded DataFrame (если задана колонка для разворота),
    - DataFrame со статусом ошибки (при сбое).
    """
    # Безопасные значения по умолчанию
    dict_columns = dict_columns or {}
    dict_explode_columns = dict_explode_columns or {}

    # Формируем URL и параметры
    url = f"{scloud_base.rstrip('/')}/{document.lstrip('/')}"
    headers = {'Accept': 'application/json'}
    params = {'$format': 'json'}

    if dict_columns:
        params['$select'] = ','.join(dict_columns.keys())
    if dttm_from_export:
        params['$filter'] = f"Date gt datetime'{dttm_from_export}'"

    # Инициализируем пустые DataFrame для возврата при ошибке
    empty_df = pd.DataFrame()
    status_df = build_status_df(
        document=document,
        status='failure',
        error_type='Error',
        error_text='Unknown error',
        error_response_text=''
    )

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
        df_raw = pd.DataFrame(data.get('value', data))

        if not dict_columns:
            # Если выборка колонок не задана, возвращаем всё как есть
            return df_raw, empty_df, empty_df

        # 1. Переименование и выборка колонок
        old_to_new = {old: new[0] for old, new in dict_columns.items()}
        df = df_raw[list(old_to_new.keys())].rename(columns=old_to_new)

        # 2. Приведение типов
        for new_col, col_info in dict_columns.items():
            # new_col здесь — новое имя (из old_to_new), но лучше брать из values
            # Используем значение из словаря: new_name = col_info[0]
            new_name = col_info[0]
            col_type = col_info[1]
            df[new_name] = update_column_type(
                df_in=df,
                column_name=new_name,
                column_type=col_type
            )

        # 3. Обработка explode-колонки
        if explode_column:
            # Определяем колонку Ref_Key (индекс или из словаря)
            ref_col = dict_columns.get('Ref_Key', [None])[0] or 'Ref_Key'
            # Убеждаемся, что ref_col существует
            if ref_col not in df.columns:
                raise ValueError(f"Ref column '{ref_col}' not found in DataFrame")

            # Разворачиваем список в отдельные строки
            df_exploded = df[[ref_col, explode_column]].explode(explode_column, ignore_index=True)

            # Нормализуем JSON-объекты в exploded-колонке
            df_normalized = pd.json_normalize(df_exploded[explode_column])

            # Если заданы спецификации для exploded-колонок, применяем их
            if dict_explode_columns:
                # Оставляем только нужные колонки и переименовываем
                df_normalized = df_normalized[list(dict_explode_columns.keys())]
                df_normalized = df_normalized.rename(
                    columns={col: spec[0] for col, spec in dict_explode_columns.items()}
                )
                # Приводим типы
                for _, spec in dict_explode_columns.items():
                    df_normalized[spec[0]] = update_column_type(df_in=df_normalized,
                                                                column_name=spec[0],
                                                                column_type=spec[1]
                                                                )

            # Соединяем exploded-данные с ref_col
            df_exploded_final = pd.concat(
                [df_exploded[[ref_col]], df_normalized],
                axis=1
            )

            # Убираем исходную explode-колонку из основного df
            df = df.drop(columns=explode_column)

            return df, df_exploded_final, empty_df

        return df, empty_df, empty_df

    except Exception as e:
        status_df = _build_failure_status_df(document, e, response=response)
        return empty_df, empty_df, status_df


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
        max_retries: int = MAX_RETRIES,
        retry_sleep_seconds: int = RETRY_SLEEP_SECONDS
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
            msg = f'Function = get_1с_data_with_retry. Document={document}. Script FAILED after {MAX_RETRIES} tries.'
            send_telegram_message(message=msg)
            write_error_to_txt(msg)
            sys.exit(1)

        sleep(retry_sleep_seconds)

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
        return 'Интеграция'
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
        return 'Услуги предикторов'
    elif 'Разработка чат-бота' in nomenclature_text:
        return 'Чат бот'
    elif 'Тест' in nomenclature_text :
        return 'Тест'
    else:
        return 'Прочее'