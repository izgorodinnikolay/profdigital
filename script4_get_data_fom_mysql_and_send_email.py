import os
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime, time
from func_import_data_from_mysql import get_df_from_db
from func_send_email import send_email


def run_get_data_fom_mysql_and_send_email():
    load_dotenv(r'C:\Users\user\Desktop\Maks\projects\invoices_2026_07_26\variables.env')

    ########################################################################################################################
    # VARIABLES

    # MySQL
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = int(os.getenv("DB_PORT"))
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_DBNAME = os.getenv("DB_DBNAME")
    DB_SUPER_USER = os.getenv("DB_SUPER_USER")

    # email
    EMAIL_FROM = os.getenv("EMAIL_FROM")
    EMAIL_TO = [item.strip() for item in os.getenv("EMAIL_TO", "").split(",") if item]
    EMAIL_PASS = os.getenv("EMAIL_PASS")

    ########################################################################################################################

    df_leads = get_df_from_db(
        db_user=DB_USER,
        db_password=DB_PASSWORD,
        db_host=DB_HOST,
        db_port=DB_PORT,
        db_dbname=DB_DBNAME,
        query=f"""select * from j28046070_sandbox.view_leads where dateAdd >= DATE_FORMAT(NOW() - INTERVAL 2 MONTH, '%Y-%m-01') order by dateTimeAdd desc""",
    )

    df_invoices = get_df_from_db(
        db_user=DB_USER,
        db_password=DB_PASSWORD,
        db_host=DB_HOST,
        db_port=DB_PORT,
        db_dbname=DB_DBNAME,
        query=f"""select * from j28046070_sandbox.view_invoices order by invoice_dt desc""",
    )

    df_invoice_report = get_df_from_db(
        db_user=DB_USER,
        db_password=DB_PASSWORD,
        db_host=DB_HOST,
        db_port=DB_PORT,
        db_dbname=DB_DBNAME,
        query=f"""select * from j28046070_sandbox.view_invoice_report order by interval_leads_minus_invoices""",
    )

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

    ########################################################################################################################

    df_description = pd.read_excel(r'C:\Users\user\Desktop\Maks\report_description.xlsx', sheet_name='description')

    ########################################################################################################################

    if time(9, 0) <= datetime.now().time() <= time(11, 0):
        send_email(
            email_from=EMAIL_FROM,
            email_to=EMAIL_TO,
            email_pass=EMAIL_PASS,
            df_description=df_description,
            df_leads=df_leads,
            df_invoices=df_invoices,
            df_invoice_report=df_invoice_report,
            df_new_invoices=df_new_invoices,
            df_payment_method=df_payment_method
        )
