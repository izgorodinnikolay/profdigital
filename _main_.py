import time

from script1_from_1C_to_mysql import run_script_from_1C_to_mysql
from script2_from_google_to_mysql import run_script_from_google_to_mysql
from script3_update_mysql_views import run_script_update_mysql_views
from script4_get_data_fom_mysql_and_send_email import run_get_data_fom_mysql_and_send_email

start_time = time.perf_counter()

run_script_from_1C_to_mysql()
run_script_from_google_to_mysql()
run_script_update_mysql_views()
run_get_data_fom_mysql_and_send_email()

end_time = time.perf_counter()
elapsed_seconds = end_time - start_time
elapsed_minutes = elapsed_seconds / 60

print(f"Script runtime: {elapsed_minutes:.2f} minutes")