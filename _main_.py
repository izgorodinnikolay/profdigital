import os
from datetime import datetime
from dotenv import load_dotenv
from zoneinfo import ZoneInfo

from func_common import get_document_structure
from func_common import send_telegram_message
from func_get_1c_data import get_1c_data_and_upload_to_mysql
from func_get_google_data import get_google_data_and_upload_to_mysql
from func_mysql_update_view import mysql_update_view_with_retry
from func_get_df_from_db import get_df_from_db_with_msg
from func_new_invoices_1c import send_errors_to_tg, send_warnings_to_tg, create_invoice_on_1c

load_dotenv('variables.env')

# 1C
SCLOUD_LOGIN = os.getenv("SCLOUD_LOGIN")
SCLOUD_PASSWORD = os.getenv("SCLOUD_PASSWORD")
SCLOUD_BASE = os.getenv("SCLOUD_BASE")
DB_SUPER_USER = os.getenv("DB_SUPER_USER")
DB_SUPER_PASSWORD = os.getenv("DB_SUPER_PASSWORD")

# MySQL
DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT"))
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_DBNAME = os.getenv("DB_DBNAME")

# Google
GOOGLE_PM_SHEET_ID = os.getenv("GOOGLE_PM_SHEET_ID")
GOOGLE_PM_GID = os.getenv("GOOGLE_PM_GID")

# technical
MAX_RETRIES = int(os.getenv("MAX_RETRIES"))
RETRY_SLEEP_SECONDS = int(os.getenv("RETRY_SLEEP_SECONDS"))
BOT_CHAT_ID_3 = os.getenv("BOT_CHAT_ID_3")
CHAT_3_TOPIC_PROCESS = os.getenv("CHAT_3_TOPIC_PROCESS")

moscow_tz = ZoneInfo("Europe/Moscow")


##############################################################################
# MAIN SCRIPT

print(f'Процесс выставления счетов запущен ({datetime.now(moscow_tz).strftime("%Y-%m-%d %H:%M:%S")})')
send_telegram_message(chat_id=BOT_CHAT_ID_3, message='Процесс выставления счетов запущен', topic_id=CHAT_3_TOPIC_PROCESS)


# 1. Выгрузка данных из 1С

print(f'1. Выгрузка данных из 1С ({datetime.now(moscow_tz).strftime("%Y-%m-%d %H:%M:%S")})')
# send_telegram_message(chat_id=BOT_CHAT_ID_3, message='1. Выгрузка данных из 1С', topic_id=CHAT_3_TOPIC_PROCESS)

documents_1c_dict = [
    'Document_СчетНаОплатуПокупателю',
    'Document_ПоступлениеНаРасчетныйСчет',
    'Document_СписаниеСРасчетногоСчета',
    'Catalog_Организации',
    'Catalog_Контрагенты',
    'Catalog_БанковскиеСчета',
    'Catalog_ДоговорыКонтрагентов',
    'Catalog_СтатьиДвиженияДенежныхСредств',
    'Catalog_Пользователи',
    'Catalog_ФизическиеЛица',
    'Catalog_Банки',
    'Catalog_Контрагенты_КонтактнаяИнформация',
    'Catalog_Организации_КонтактнаяИнформация',
]

for document in documents_1c_dict:
    get_1c_data_and_upload_to_mysql(
        scloud_base=SCLOUD_BASE,
        scloud_user=SCLOUD_LOGIN,
        scloud_password=SCLOUD_PASSWORD,
        document=document,
        db_user=DB_USER,
        db_password=DB_PASSWORD,
        db_host=DB_HOST,
        db_port=DB_PORT,
        db_dbname=DB_DBNAME,
        truncate=True,
        dttm_from_export='',
        max_retries=MAX_RETRIES,
        retry_sleep_seconds=RETRY_SLEEP_SECONDS
    )


# 2. Выгрузка данных из Google по способу оплаты

print(f'2. Выгрузка данных из Google по способу оплаты ({datetime.now(moscow_tz).strftime("%Y-%m-%d %H:%M:%S")})')
# send_telegram_message(chat_id=BOT_CHAT_ID_3, message='2. Выгрузка данных из Google по способу оплаты', topic_id=CHAT_3_TOPIC_PROCESS)

get_google_data_and_upload_to_mysql(
    google_pm_sheet_id=GOOGLE_PM_SHEET_ID,
    google_pm_gid=GOOGLE_PM_GID,
    google_config='payment_method',
    db_user=DB_USER,
    db_password=DB_PASSWORD,
    db_host=DB_HOST,
    db_port=DB_PORT,
    db_dbname=DB_DBNAME,
    truncate=True,
    max_retries=MAX_RETRIES,
    retry_sleep_seconds=RETRY_SLEEP_SECONDS
)


# 3. Обновление объектов на ProfDigital

print(f'3. Обновление объектов на ProfDigital ({datetime.now(moscow_tz).strftime("%Y-%m-%d %H:%M:%S")})')
# send_telegram_message(chat_id=BOT_CHAT_ID_3, message='3. Обновление объектов на ProfDigital', topic_id=CHAT_3_TOPIC_PROCESS)

mysql_tables_list = [
    ["j28046070_sandbox", "view_leads"],
    ["j28046070_sandbox", "view_payment_method"],
    ["j28046070_sandbox", "view_invoices"],
    ["j28046070_sandbox", "view_invoice_report"],
]

for tbl in mysql_tables_list:
    mysql_update_view_with_retry(
        db_user=DB_SUPER_USER,
        db_password=DB_SUPER_PASSWORD,
        db_host=DB_HOST,
        db_port=DB_PORT,
        db_dbname=DB_SUPER_USER,
        tbl_db=tbl[0],
        tbl_name=tbl[1],
        big_query_flag=True,
        max_retries=5,
        retry_sleep_seconds=30
    )


# 4. Выгрузка обновленных данных из ProfDigital

print(f'4. Выгрузка обновленных данных из ProfDigital ({datetime.now(moscow_tz).strftime("%Y-%m-%d %H:%M:%S")})')
# send_telegram_message(chat_id=BOT_CHAT_ID_3, message='4. Выгрузка обновленных данных из ProfDigital', topic_id=CHAT_3_TOPIC_PROCESS)

excel_sheet_names_dict = {
    'df_invoice_report': 'Баланс счетов',
    'df_new_invoices': 'Выставление счетов',
    'df_errors': 'Ошибки в счетах счетов',
    'df_payment_method': 'Способ оплаты'
}

dataframes = dict()

df_output_config = get_document_structure('df_output')

for df, query in df_output_config.items():
    dataframes[df] = get_df_from_db_with_msg(
        db_user=DB_USER,
        db_password=DB_PASSWORD,
        db_host=DB_HOST,
        db_port=DB_PORT,
        db_dbname=DB_DBNAME,
        query=query,
        df=df
    )


# 5. Выставление счетов

print(f'5. Выставление счетов ({datetime.now(moscow_tz).strftime("%Y-%m-%d %H:%M:%S")})')
# send_telegram_message(chat_id=BOT_CHAT_ID_3, message='5. Выставление счетов', topic_id=CHAT_3_TOPIC_PROCESS)

df = dataframes['df_invoice_report'].copy()


if datetime.strptime("09:50", "%H:%M").time() <= datetime.now().time() <= datetime.strptime("11:50", "%H:%M").time():

    ### 5.1. Отправка сообщений об ошибках
    print(f'    5.1. Отправка сообщений об ошибках')
    # send_telegram_message(chat_id=BOT_CHAT_ID_3, message='Отправка сообщений об ошибках', topic_id=CHAT_3_TOPIC_PROCESS)

    criteria_errors = (
        (~df.inn.isin(['7840087426', '720306065102'])) &
        (df.new_invoice_flag == 'Нет') &
        (df.stop_flg.str.lower().fillna('') != 'на стопе') &
        (((df.prev_cnt > 0) & (df.interval_sale > 0) & (df.project == 'нет инфо')) |
         ((df.prev_cnt > 0) & (df.interval_sale > 0) & (df.partner_id.isna())) |
         ((df.prev_cnt > 0) & (df.interval_sale > 0) & (df.contract_id.isna()))
         )
    )

    for row in df[criteria_errors].to_dict(orient='records'):
        send_errors_to_tg(row)


    ### 5.2. Отправка уведомлений
    print(f'    5.2. Отправка уведомлений')
    # send_telegram_message(chat_id=BOT_CHAT_ID_3, message='Отправка уведомлений', topic_id=CHAT_3_TOPIC_PROCESS)

    criteria_warnings = (
        (~df.inn.isin(['7840087426', '720306065102'])) &
        (df.new_invoice_flag == 'Нет') &
        (df.stop_flg.str.lower().fillna('') != 'на стопе') &
        (df.project != 'нет инфо') &
        (~df.partner_id.isna()) &
        (~df.contract_id.isna()) &
        (df.prev_cnt > 0) &
        (((df.payment_type == 'депозит') &
          (df.interval_invoices_minus_leads <= df.deposit_min_value * 2)) |
         (df.interval_invoices_minus_leads < 0))
    )

    for row in df[criteria_warnings].to_dict(orient='records'):
        send_warnings_to_tg(row)


### 5.3. Выставление счетов
print(f'    5.3. Выставление счетов')
# send_telegram_message(chat_id=BOT_CHAT_ID_3, message='Выставление счетов', topic_id=CHAT_3_TOPIC_PROCESS)

criteria_new_invoice = ((df.new_invoice_flag == 'Да') & (df.stop_flg.str.lower().fillna('') != 'на стопе'))

for row in df[criteria_new_invoice].to_dict(orient='records'):
    create_invoice_on_1c(
        scloud_base=SCLOUD_BASE,
        scloud_login=SCLOUD_LOGIN,
        scloud_password=SCLOUD_PASSWORD,
        inn_data=row
    )

if len(df[criteria_new_invoice]) == 0:
    invoices_msg = 'Новых счетов нет'
elif len(df[criteria_new_invoice]) == 1:
    invoices_msg = 'Выставлен 1 счет'
elif len(df[criteria_new_invoice]) < 5:
    invoices_msg = f'Выставлено {len(df[criteria_new_invoice])} счета'
else:
    invoices_msg = f'Выставлено {len(df[criteria_new_invoice])} счетов'

print(f'{invoices_msg}')
send_telegram_message(chat_id=BOT_CHAT_ID_3, message=invoices_msg, topic_id=CHAT_3_TOPIC_PROCESS)

print(f'Процесс выставления счетов завершен ({datetime.now(moscow_tz).strftime("%Y-%m-%d %H:%M:%S")})')
send_telegram_message(chat_id=BOT_CHAT_ID_3, message='Процесс выставления счетов завершен', topic_id=CHAT_3_TOPIC_PROCESS)
