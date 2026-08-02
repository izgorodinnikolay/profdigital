import io
import pandas as pd
import smtplib
from datetime import date
from email.message import EmailMessage


def send_email(
        email_from: str,
        email_to: list,
        email_pass: str,
        df_description,
        df_leads,
        df_invoices,
        df_invoice_report,
        df_new_invoices,
        df_payment_method
):

    message = EmailMessage()

    # Add standard headers
    message["From"] = email_from  # sender_email
    message["To"] = ', '.join(email_to)  # receiver_email
    message["Subject"] = f'Отчет по счетам за {date.today().strftime("%Y-%m-%d")}'  # subject

    # Set the plain text body
    message.set_content(f'Привет!\n\nОтправляю отчет на {date.today().strftime("%Y-%m-%d")}.')

    excel_buffer = io.BytesIO()

    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
        df_description.to_excel(writer, sheet_name='Описание', index=False)
        df_leads.to_excel(writer, sheet_name='Лиды', index=False)
        df_invoices.to_excel(writer, sheet_name='Оплата счетов', index=False)
        df_invoice_report.to_excel(writer, sheet_name='Баланс счетов', index=False)
        df_new_invoices.to_excel(writer, sheet_name='Выставление счетов', index=False)
        df_payment_method.to_excel(writer, sheet_name='Способ оплаты', index=False)

    excel_buffer.seek(0)
    excel_data = excel_buffer.getvalue()

    # Notice 'rb'
    # with open(filename, 'rb') as attachment:
    message.add_attachment(excel_data,
                           maintype='application',
                           subtype='vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                           filename=f'Отчет по счетам {date.today().strftime("%Y-%m-%d")}.xlsx'
                           )

    # AGAIN, no need for a context if you are just using the default SSL
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.ehlo()  # Identify yourself to the server
        server.starttls()  # 🔒 Upgrade connection to secure TLS
        server.ehlo()  # Re-identify over the secure channel
        server.login(email_from, email_pass)
        server.send_message(message)