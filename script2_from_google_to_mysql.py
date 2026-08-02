import os
from dotenv import load_dotenv
from func_import_data_from_google import get_google_payment_method
from func_import_data_from_1c import export_df_to_db_with_retry

def run_script_from_google_to_mysql():

    load_dotenv(r'C:\Users\user\Desktop\Maks\projects\invoices_2026_07_26\variables.env')

    ########################################################################################################################
    # VARIABLES

    # MySQL
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = int(os.getenv("DB_PORT"))
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_DBNAME = os.getenv("DB_DBNAME")

    ########################################################################################################################

    GOOGLE_PM_SHEET_ID, GOOGLE_PM_GID = "1fjnZPcmcmgSuRBDPfjUYY30-t_vG1Kt2VPt4r2_mJBY", "0" # адрес google-таблицы
    GOOGLE_PM_COLUMNS = {
        'Ответственный' : ['project', 'string'],
        'Юр. лицо (ИП/ООО)' : ['legal_entity', 'string'],
        'ИНН' : ['inn', 'string'],
        # 'Компания',
        # 'Где размещены',
        'Порог остатка' : ['deposit_min_value', 'string'],
        'Средний размер депозитов' : ['deposit_average_value', 'string'],
        'Депозит' : ['deposit_current_value', 'string'],
        # 'Сслыка на таблицу', 'Количество источников', 'Unnamed: 10', 'Unnamed: 11', 'Unnamed: 12', 'Сводная', 'Ставка продажи', 'Ставка покупки',
        'Депозит.1' : ['payment_type', 'string'],
        # 'Почта клиента',
        # 'Ссылка на таблицу отчёта сейчас, если есть',
        # 'Комментарий - в каком формате нужна выгрузка (по каждому ИП, по компании, по источнику и тд)'
    }
    DB_TABLE = 'payment_method' # таблица на MySQL, куда выгружаем данные


    payment_method = \
    get_google_payment_method(
        google_pm_sheet_id=GOOGLE_PM_SHEET_ID,
        google_pm_gid=GOOGLE_PM_GID,
        google_pm_columns=GOOGLE_PM_COLUMNS
    )

    export_df_to_db_with_retry(
        df_src=payment_method,
        db_user=DB_USER,
        db_password=DB_PASSWORD,
        db_host=DB_HOST,
        db_port=DB_PORT,
        db_dbname=DB_DBNAME,
        db_table=DB_TABLE,
        truncate=True
    )