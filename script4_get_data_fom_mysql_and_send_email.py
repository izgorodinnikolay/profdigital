import os
import pandas as pd
from dotenv import load_dotenv

from datetime import datetime, time as dt_time  # Импортируем время из datetime под именем dt_time
from func_common import send_telegram_message
from func_import_data_from_mysql import get_df_from_db
from func_send_email import send_email
from func_new_invoices_1c import create_invoice_on_1c


def run_get_data_fom_mysql_and_send_email():

    try:

        load_dotenv('variables.env')

        ########################################################################################################################
        # VARIABLES

        # MySQL
        DB_HOST = os.getenv("DB_HOST")
        DB_PORT = int(os.getenv("DB_PORT"))
        DB_USER = os.getenv("DB_USER")
        DB_PASSWORD = os.getenv("DB_PASSWORD")
        DB_DBNAME = os.getenv("DB_DBNAME")
        DB_SUPER_USER = os.getenv("DB_SUPER_USER")

        # 1C
        SCLOUD_LOGIN = os.getenv("SCLOUD_LOGIN")
        SCLOUD_PASSWORD = os.getenv("SCLOUD_PASSWORD")
        SCLOUD_BASE = os.getenv("SCLOUD_BASE")

        # email
        EMAIL_FROM = os.getenv("EMAIL_FROM")
        EMAIL_TO = [item.strip() for item in os.getenv("EMAIL_TO", "").split(",") if item]
        EMAIL_PASS = os.getenv("EMAIL_PASS")

        print(f'starting run_script_update_mysql_views')

        ########################################################################################################################

        df_invoice_report = get_df_from_db(
            db_user=DB_USER,
            db_password=DB_PASSWORD,
            db_host=DB_HOST,
            db_port=DB_PORT,
            db_dbname=DB_DBNAME,
            query=f"""select * from j28046070_sandbox.view_invoice_report order by interval_leads_minus_invoices""",
        )

        if dt_time(5, 0) <= datetime.now().time() <= dt_time(7, 0) or \
                dt_time(15, 0) <= datetime.now().time() <= dt_time(17, 0):

            for row in df_invoice_report[
                (df_invoice_report.project == 'Даша') & \
                (df_invoice_report.payment_type == 'депозит') & \
                (df_invoice_report.total_deposit_balance > df_invoice_report.deposit_min_value) & \
                (df_invoice_report.total_deposit_balance <= df_invoice_report.deposit_min_value * 2) & \
                (~df_invoice_report["new_invoice_description"].str.contains("Нет лидов с", na=False))
            ].to_dict(orient='records'):

                city_str = f", город = {row['city_invoice']}" if len(row['city_invoice']) > 0 else ""
                comment = (
                    "массаж"
                    if row['source_invoice'] == "РМ"
                    else ("Александрит" if row['source_invoice'] == "АЛЭ" else "нет")
                )
                calc_detailes1 = (
                    f"ОСТАТОК = {row['interval_deposit_balance']:_.0f}\n"
                    f"минимальный депозит = {row['deposit_min_value']:_.0f}\n"
                    f"средний депозит = {row['deposit_average_value']:_.0f}"
                ).replace("_", " ")
                calc_detailes2 = (
                    f"стоимость лидов = {row['interval_sale']:_.0f}\n"
                    f"сумма счетов = {max(row['interval_invoice'], row['interval_receipt']):_.0f}\n"
                    f"корректировка = {row['interval_correction']:_.0f}\n"
                ).replace("_", " ")

                msg = (
                    f"*'{row['legal_entity']}'*\n"
                    f"(ИНН = {row['inn']}{city_str}, комментарий = '{comment}')\n\n"
                    f"*ПРИБЛИЖАЕТСЯ ОПЛАТА*\n\n"
                    f"{calc_detailes1}\n\n"
                    f"_детализация расчетов:_\n\n"
                    f"тип оплаты = {row['payment_type']}\n"
                    f"{calc_detailes2}"
                )
                # print(msg)
                send_telegram_message(message=msg)

        if dt_time(9, 0) <= datetime.now().time() <= dt_time(11, 0):

            df_payment_method = get_df_from_db(
                db_user=DB_USER,
                db_password=DB_PASSWORD,
                db_host=DB_HOST,
                db_port=DB_PORT,
                db_dbname=DB_DBNAME,
                query=f"""select * from j28046070_sandbox.view_payment_method""",
            )

            df_new_invoices = get_df_from_db(
                db_user=DB_USER,
                db_password=DB_PASSWORD,
                db_host=DB_HOST,
                db_port=DB_PORT,
                db_dbname=DB_DBNAME,
                query=f"""select * from j28046070_sandbox.view_new_invoices order by new_invoice_flag, interval_leads_minus_invoices""",
            )

            df_errors = get_df_from_db(
                db_user=DB_USER,
                db_password=DB_PASSWORD,
                db_host=DB_HOST,
                db_port=DB_PORT,
                db_dbname=DB_DBNAME,
                query=f"""with 
                        tmp as (
                            select case when inn = '7840087426' then 'Кривой процесс выставления счетов - по 260к - выставляем руками'
                                        when project = 'нет инфо' then 'Заполнить инфо в Google'
                                        when project != 'Даша' then 'Пока не выставляем счета по ПМ, кроме Даши'
                                        when partner_id is not null then 'Отсутствуют данные в Catalog_Контрагенты'
                                        when contract_id is not null then 'Отсутствуют данные в Catalog_ДоговорыКонтрагентов'
                                        else 'Доработать'
                                end as reason
                                ,inn, project, legal_entity
                                ,payment_type, deposit_min_value, deposit_average_value
                                ,interval_cnt, interval_purchase, interval_sale, interval_invoice, interval_receipt, interval_correction, interval_leads_minus_invoices, interval_deposit_balance
                                ,new_invoice_flag, new_invoice_description, new_invoice_amount
                            from j28046070_sandbox.view_invoice_report
                            where interval_leads_minus_invoices < deposit_min_value or new_invoice_flag = 'Да')
                        select * from tmp where reason is not null """
            )

            ########################################################################################################################

            df_description = pd.read_excel(r'C:\Users\user\Desktop\Maks\report_description.xlsx', sheet_name='description')

            ########################################################################################################################

            fields_new_invoices = \
                ['inn', 'project', 'legal_entity', 'payment_type', 'deposit_min_value', 'deposit_average_value',
                 'interval_cnt',
                 'interval_purchase',
                 'interval_sale', 'interval_invoice', 'interval_receipt', 'interval_correction',
                 'interval_leads_minus_invoices', 'interval_deposit_balance',
                 'new_invoice_flag', 'new_invoice_description', 'new_invoice_amount']

            send_email(
                email_from=EMAIL_FROM,
                email_to=EMAIL_TO,
                email_pass=EMAIL_PASS,
                df_description=df_description,
                df_invoice_report=df_invoice_report,
                df_new_invoices=df_new_invoices[fields_new_invoices],
                df_errors=df_errors,
                df_payment_method=df_payment_method
            )

            if len(df_new_invoices) > 0:
                invoice_results = \
                    create_invoice_on_1c(
                        scloud_base=SCLOUD_BASE,
                        scloud_login=SCLOUD_LOGIN,
                        scloud_password=SCLOUD_PASSWORD,
                        df_new_invoices=df_new_invoices
                    )
            else:
                invoice_results = {}

            if len(invoice_results) == 0:
                invoices_msg = 'Новых счетов нет'
            elif len(invoice_results) == 1:
                invoices_msg = 'Выставлен 1 счет'
            elif len(invoice_results) < 5:
                invoices_msg = f'Выставлено {len(invoice_results) } счета'
            else:
                invoices_msg = f'Выставлено {len(invoice_results)} счетов'

            send_telegram_message(message='Процесс выставления счетов завершен\n' + invoices_msg)

        else:
            send_telegram_message(message='Процесс отработал без выставления счетов счетов')


    except Exception as e:

        send_telegram_message(message = f'Процесс упал на этапе выставления счетов.\nОшибка {e[0:1000]}')






