from datetime import datetime, time as dt_time  # Импортируем время из datetime под именем dt_time
import time

from script1_from_1C_to_mysql import run_script_from_1C_to_mysql
from script2_from_google_to_mysql import run_script_from_google_to_mysql
from script3_update_mysql_views import run_script_update_mysql_views
from script4_get_data_fom_mysql_and_send_email import run_get_data_fom_mysql_and_send_email
from func_common import send_telegram_message

start_time = time.perf_counter()

run_script_from_1C_to_mysql()
run_script_from_google_to_mysql()
run_script_update_mysql_views()

if dt_time(9, 0) <= datetime.now().time() <= dt_time(11, 0):
    invoices = run_get_data_fom_mysql_and_send_email()

    if len(invoices) == 0:
        invoices_msg = 'Новых счетов нет'
    elif len(invoices) == 1:
        invoices_msg = 'Выставлен 1 счет'
    elif len(invoices) < 5:
        invoices_msg = f'Выставлено {len(invoices) } счета'
    else:
        invoices_msg = f'Выставлено {len(invoices)} счетов'

    send_telegram_message(message='Процесс выставления счетов завершен\n'+invoices_msg)

else:
    send_telegram_message(message='Процесс отработал без выставления счетов счетов')

end_time = time.perf_counter()
elapsed_seconds = end_time - start_time
elapsed_minutes = elapsed_seconds / 60

print(f"Script runtime: {elapsed_minutes:.2f} minutes")