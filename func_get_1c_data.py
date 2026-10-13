import pandas as pd
import requests
import os
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth
from time import sleep as sys_sleep
from typing import Dict, List, Tuple, Optional, Any

from func_common import log_errors, send_telegram_message, get_document_structure
from func_export_df_to_db import export_df_to_db_with_retry

load_dotenv('variables.env')

MAX_RETRIES = int(os.getenv("MAX_RETRIES"))
RETRY_SLEEP_SECONDS = int(os.getenv("RETRY_SLEEP_SECONDS"))
BOT_CHAT_ID_3 = os.getenv("BOT_CHAT_ID_3")
CHAT_3_TOPIC_PROCESS = os.getenv("CHAT_3_TOPIC_PROCESS")


def update_column_type(df_in: pd.DataFrame, column_name: str, column_type: str):
    if column_type == 'datetime':
        return df_in[column_name].replace(['0', 0, '0000-00-00', '0000-00-00 00:00:00', ''], pd.NA).apply(pd.to_datetime, utc=True, errors='coerce')
    elif column_type in ['int', 'float']:
        return df_in[column_name].fillna(0).astype(column_type)
    elif column_type in ['string', 'boolean']:
        return df_in[column_name].astype(column_type)
    else:
        return df_in[column_name]


def get_1c_data(
    scloud_base: str,
    scloud_user: str,
    scloud_password: str,
    document: str,
    dict_columns: Optional[Dict[str, List[Any]]] = None,
    explode_column: str = '',
    dict_explode_columns: Optional[Dict[str, List[Any]]] = None,
    dttm_from_export: str = ''
) -> Tuple[pd.DataFrame, pd.DataFrame]:
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

    response = requests.get(
        url=url,
        headers=headers,
        params=params,
        auth=HTTPBasicAuth(scloud_user, scloud_password),
        timeout=90
    )
    response.raise_for_status()
    data = response.json()
    df_raw = pd.DataFrame(data.get('value', data))

    if not dict_columns:
        return df_raw, pd.DataFrame()

    old_to_new = {old: new[0] for old, new in dict_columns.items()}
    df = df_raw[list(old_to_new.keys())].rename(columns=old_to_new)

    for new_col, col_info in dict_columns.items():
        new_name = col_info[0]
        col_type = col_info[1]
        df[new_name] = update_column_type(
            df_in=df,
            column_name=new_name,
            column_type=col_type
        )

    if explode_column:
        ref_col = dict_columns.get('Ref_Key', [None])[0] or 'Ref_Key'
        if ref_col not in df.columns:
            raise ValueError(f"Ref column '{ref_col}' not found in DataFrame")

        df_exploded = df[[ref_col, explode_column]].explode(explode_column, ignore_index=True)

        df_normalized = pd.json_normalize(df_exploded[explode_column])

        if dict_explode_columns:
            df_normalized = df_normalized[list(dict_explode_columns.keys())]
            df_normalized = df_normalized.rename(
                columns={col: spec[0] for col, spec in dict_explode_columns.items()}
            )
            for _, spec in dict_explode_columns.items():
                df_normalized[spec[0]] = update_column_type(df_in=df_normalized,
                    column_name=spec[0],
                    column_type=spec[1]
                )

        df_exploded_final = pd.concat(
            [df_exploded[[ref_col]], df_normalized],
            axis=1
        )

        df = df.drop(columns=explode_column)

        return df, df_exploded_final

    return df, pd.DataFrame()


@log_errors
def get_1c_data_with_retry(
        scloud_base: str,
        scloud_user: str,
        scloud_password: str,
        document: str,
        dict_columns: dict = {},
        explode_column: str = '',
        dict_explode_columns: dict = {},
        dttm_from_export: str = '',
        max_retries: int = 5,
        retry_sleep_seconds: int = 180
):
    for attempt in range(1, max_retries + 1):

        try:

            df, df_exploded = get_1c_data(
                scloud_base=scloud_base,
                scloud_user=scloud_user,
                scloud_password=scloud_password,
                document=document,
                dict_columns=dict_columns,
                explode_column=explode_column,
                dict_explode_columns=dict_explode_columns,
                dttm_from_export=dttm_from_export
            )

            return df, df_exploded

        except Exception as e:

            msg = f"Function GET_1С_DATA FAILED to load document={document}. Attempt={attempt}/{max_retries}."
            print(msg)

            if attempt == max_retries:
                msg = (
                    f"Function GET_1С_DATA FAILED to load document={document} after {max_retries} tries."
                    f"Last error: {str(e)}"
                )

                send_telegram_message(chat_id=BOT_CHAT_ID_3, message=msg, topic_id=CHAT_3_TOPIC_PROCESS)
                raise RuntimeError(msg)

            sys_sleep(retry_sleep_seconds)

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
        return 'Услуги предикторов'
    elif 'Разработка чат-бота' in nomenclature_text:
        return 'Чат бот'
    elif 'Тест' in nomenclature_text :
        return 'Тест'
    else:
        return 'Прочее'


@log_errors
def get_1c_data_and_upload_to_mysql(
        scloud_base: str,
        scloud_user: str,
        scloud_password: str,
        document: str,
        db_user: str,
        db_password: str,
        db_host: str,
        db_port: int,
        db_dbname: str,
        truncate: bool = True,
        dttm_from_export: str = '',
        max_retries: int = 5,
        retry_sleep_seconds: int = 90,
        notification_flg: bool = False
):
    process_msg = f'upload data from 1C {document}'
    print(f'  {process_msg}')

    if notification_flg:
        send_telegram_message(chat_id=BOT_CHAT_ID_3, message=process_msg, topic_id=CHAT_3_TOPIC_PROCESS)

    config_vars = get_document_structure(document)

    mysql_tbl = config_vars.get('MYSQL_TBL', '')
    mysql_tbl_detailed = config_vars.get('MYSQL_TBL_DETAILED', '')
    dict_columns = config_vars.get('DICT_COLUMNS', None)
    explode_column = config_vars.get('EXPLODE_COLUMN')
    dict_explode_columns = config_vars.get('DICT_EXPLODE_COLUMNS', None)

    df, df_detailed = get_1c_data_with_retry(
        scloud_base=scloud_base,
        scloud_user=scloud_user,
        scloud_password=scloud_password,
        document=document,
        dict_columns=dict_columns,
        explode_column=explode_column,
        dict_explode_columns=dict_explode_columns,
        dttm_from_export='',  # DTTM_FROM_EXPORT
        max_retries=max_retries,
        retry_sleep_seconds=retry_sleep_seconds
    )

    export_df_to_db_with_retry(
        df_src=df,
        db_user=db_user,
        db_password=db_password,
        db_host=db_host,
        db_port=db_port,
        db_dbname=db_dbname,
        db_table=mysql_tbl,
        truncate=truncate
    )

    if mysql_tbl_detailed != '':

        if mysql_tbl_detailed == 'invoice_detailed_1c':
            df_detailed['nomenclature_text_gr'] = [*map(nomenclature_text_gr, df_detailed.nomenclature_text)]

        export_df_to_db_with_retry(
            df_src=df_detailed,
            db_user=db_user,
            db_password=db_password,
            db_host=db_host,
            db_port=db_port,
            db_dbname=db_dbname,
            db_table=mysql_tbl_detailed,
            truncate=truncate
        )