import html
import json
import os
import pandas as pd
import requests

from datetime import datetime
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth
from time import sleep as sys_sleep

from func_common import log_errors, send_telegram_message, float_rus_format

load_dotenv('variables.env')

BOT_CHAT_ID_3 = os.getenv("BOT_CHAT_ID_3")
CHAT_3_TOPIC_PROCESS = os.getenv("CHAT_3_TOPIC_PROCESS")
CHAT_3_TOPIC_ALARM = os.getenv("CHAT_3_TOPIC_ALARM")
CHAT_3_TOPIC_PAYMENT_SOON = os.getenv("CHAT_3_TOPIC_PAYMENT_SOON")
CHAT_3_TOPIC_NEW_INVOICES = os.getenv("CHAT_3_TOPIC_NEW_INVOICES")


def project_managers_tg(project_manager: str) -> str:
    project_managers = {
        'Даша': '@er_daria',
        'Женя': '@evgendobrohleb',
        'Света': '@ssbykovaa',
        'Катя': '@Parvii87',
        'Никита': '@Nikita_Kopyrin'
    }
    manager_username = project_managers.get(project_manager, '')
    return f"({manager_username})" if manager_username else ''


@log_errors
def send_errors_to_tg(inn_data: dict) -> None:
    safe_legal_entity = html.escape(str(inn_data.get('legal_entity', '')))
    safe_city = html.escape(str(inn_data.get('city_invoice', '')))

    pm_comment_val = inn_data.get('pm_comment', '')
    if pd.isna(pm_comment_val) or str(pm_comment_val).strip() == '' or str(pm_comment_val) == 'None':
        project_comment = ''
    else:
        project_comment = f"ПМ коммент: {html.escape(str(pm_comment_val))}"

    project_name = inn_data.get('project', 'нет инфо')
    if project_name == 'нет инфо':
        project = 'Таинственный Незнакомец'
    else:
        project = f"PM {html.escape(str(project_name))} {project_managers_tg(project_name)}"

    accountant = f", Валя (@tina_bogomol)" if pd.isna(inn_data.get('partner_id')) or pd.isna(
        inn_data.get('contract_id')) else ''

    city_str = f", город = {safe_city}" if len(safe_city) > 0 else ""

    source = inn_data.get('source_invoice', '')
    comment = "массаж" if source == "РМ" else ("Александрит" if source == "АЛЭ" else "нет")

    problem1 = f"- По клиенту нет инфо в Google-таблице\n" if project_name == 'нет инфо' else ''
    problem2 = f"- В 1С нет инфо по клиенту (Catalog_Контрагенты)\n" if pd.isna(inn_data.get('partner_id')) else ''
    problem3 = f"- В 1С нет инфо по договору (Catalog_ДоговорыКонтрагентов)\n" if pd.isna(
        inn_data.get('contract_id')) else ''

    msg = (
        f"<b>{project}{accountant}</b>\n\n"
        f"<b>'{safe_legal_entity}'</b>\n"
    )

    if project_comment:
        msg += f"<b>{project_comment}</b>\n"

    msg += (
        f"(ИНН = {inn_data.get('inn')}{city_str}, комментарий = '{comment}')\n\n"
        f"<b>!!! НЕ МОГУ ВЫСТАВИТЬ СЧЕТ !!!</b>\n\n"
        f"Проблемы:\n{problem1}{problem2}{problem3}\n"
        f"Детализация:\n\n"
        f"стоимость лидов = {float_rus_format(inn_data.get('interval_sale', 0))}\n"
        f"сумма счетов = {float_rus_format(max(inn_data.get('interval_invoice', 0), inn_data.get('interval_receipt', 0)))}\n"
        f"корректировка = {float_rus_format(inn_data.get('interval_correction', 0))}\n\n"
        f"ИТОГО БАЛАНС = {float_rus_format(inn_data.get('interval_invoices_minus_leads', 0))}"
    )

    # print('---------------------------------------------\n', msg)
    send_telegram_message(chat_id=BOT_CHAT_ID_3, message=msg, topic_id=CHAT_3_TOPIC_ALARM)
    sys_sleep(5)


@log_errors
def send_warnings_to_tg(inn_data: dict) -> None:
    project = f"PM {inn_data['project']} {project_managers_tg(inn_data['project'])}"

    project_comment = f"ПМ коммент: {inn_data['pm_comment']}\n" if inn_data['pm_comment'] != '' else ''

    city_str = f", город = {inn_data['city_invoice']}" if len(inn_data['city_invoice']) > 0 else ""
    comment = (
        "массаж"
        if inn_data['source_invoice'] == "РМ"
        else ("Александрит" if inn_data['source_invoice'] == "АЛЭ" else "нет")
    )

    pmnt_msg = f"<b>ПРИБЛИЖАЕТСЯ ОПЛАТА</b>" \
        if inn_data['interval_invoices_minus_leads'] >= inn_data['deposit_min_value'] else \
        ('<b>СУММА СЧЁТА МЕНЬШЕ СТОИМОСТИ ЛИДОВ</b>' if inn_data['payment_type'] != 'депозит' \
             else f"<b>ОПЛАТА ПРОСРОЧЕНА</b>")

    deposit_details = (
        f"минимальный депозит = {float_rus_format(inn_data['deposit_min_value'])}\n"
        f"средний депозит = {float_rus_format(inn_data['deposit_average_value'])}\n\n"
    ) if inn_data['payment_type'] == 'депозит' else ""

    reason = f"Причина (если есть): {inn_data['new_invoice_errors']}" if inn_data['new_invoice_errors'] != '' else ''

    msg = (
        f"<b>{project}</b>\n\n"
        f"<b>'{inn_data['legal_entity']}'</b>\n"
        f"<b>{project_comment}</b>"
        f"(ИНН = {inn_data['inn']}{city_str}, комментарий = '{comment}')\n\n"
        f"{pmnt_msg}\n\n"
        f"БАЛАНС = {float_rus_format(inn_data['interval_invoices_minus_leads'])}\n\n"
        f"<i>детализация расчетов:</i>\n\n"
        f"тип оплаты = {inn_data['payment_type']}\n"
        f"{deposit_details}"  # Вставится с переносами, только если тип 'депозит'
        f"стоимость лидов = {float_rus_format(inn_data['interval_sale'])}\n"
        f"сумма счетов = {float_rus_format(max(inn_data['interval_invoice'], inn_data['interval_receipt']))}\n"
        f"корректировка = {float_rus_format(inn_data['interval_correction'])}\n\n"
        f"{reason}"
    )

    # print(msg)
    send_telegram_message(chat_id=BOT_CHAT_ID_3, message=msg, topic_id=CHAT_3_TOPIC_PAYMENT_SOON)

    sys_sleep(5)


def create_invoice(scloud_base: str,
                   scloud_login: str,
                   scloud_password: str,
                   inn_data: dict
                   ):
    document = 'Document_СчетНаОплатуПокупателю'
    url = f'{scloud_base}/{document}'
    headers = {'Authorization': 'Basic', 'Accept': 'application/json'}

    comment = (
        'массаж' if inn_data['source_invoice'] == 'РМ' else (
        'Александрит' if inn_data['source_invoice'] == 'АЛЭ' else (
        inn_data['city_invoice'] if inn_data['city_invoice'] in ('Алматы', 'Улан-Удэ') else ''))
    )
    nomenclature = (
        'Оплата стоимости лидов (депозит)' if inn_data['payment_type'] == 'депозит' else
        'Оплата стоимости лидов'
    )
    price = (
        inn_data['new_invoice_amount'] if inn_data['payment_type'] == 'депозит' else
        round(inn_data['interval_sale'] / inn_data['interval_cnt'], 2)
    )
    cnt = 0 if inn_data['payment_type'] == 'депозит' else inn_data['interval_cnt']

    document_data = {
        'Date': datetime.strftime(datetime.now(), '%Y-%m-%dT%H:%M:%S'),
        'Posted': True,

        # из 1С
        'СтруктурнаяЕдиница_Key': '6efcc024-92da-11f0-96c0-00155d46f8c2',  # 40802810200008615630, АО "ТИНЬКОФФ БАНК"
        'Ответственный_Key': 'dcbbf600-1c57-11f1-8778-00155d46fc0e',  # dop0265986

        # Из MySQL
        'Контрагент_Key': inn_data['partner_id'],
        'ДоговорКонтрагента_Key': inn_data['contract_id'],
        'СуммаДокумента': ['new_invoice_amount'],
        'Организация_Key': inn_data['organization_id'],  # ИП Бушуева Е. Б.
        'ОрганизацияПолучатель_Key': inn_data['organization_id'],  # ИП Бушуева Е. Б.
        'Руководитель_Key': inn_data['manager_key'],  # Бушуева Елена Борисовна
        'Комментарий': comment,

        # константы
        'ВалютаДокумента_Key': '9838a908-78df-11e8-80df-0050569f2e9f',
        'ДополнительныеУсловия_Key': 'a077deef-78df-11e8-80df-0050569f2e9f',  # Типовые условия
        'СпособДоставки_Key': '3321a217-b558-11ec-a1c3-00155d46ae10',  # Самовывоз
        # 'УдалитьУчитыватьНДС': True, #
        'ДокументБезНДС': False,
        'ВидОперации': 'ТоварыИУслуги',
        'ВариантПечатиQRКода': 'НеПечатать',  # уточнить
        'Товары': [{
            'LineNumber': '1',
            'Номенклатура': '44d84e8c-ab20-11ef-8a67-00155d46f8c3',
            'Номенклатура_Type': 'StandardODATA.Catalog_Номенклатура',
            'Содержание': nomenclature,
            'Количество': cnt,
            'Цена': price,
            'Сумма': inn_data['new_invoice_amount'],
            'ПроцентСкидки': 0,
            'СуммаСкидки': 0,
            'СтавкаНДС': 'НДС5',
            'СуммаНДС': int(inn_data['new_invoice_amount'] * 5 / 105 * 100) / 100}]
    }

    response = requests.post(url, headers=headers, data=json.dumps(document_data),
                             auth=HTTPBasicAuth(scloud_login, scloud_password))

    return response.status_code


@log_errors
def create_invoice_on_1c(
        scloud_base: str,
        scloud_login: str,
        scloud_password: str,
        inn_data: dict
) -> None:
    invoice_output = dict()

    project = f"PM {inn_data['project']} {project_managers_tg(inn_data['project'])}"

    project_comment = f"ПМ коммент: {inn_data['pm_comment']}\n" if inn_data['pm_comment'] != '' else ''

    city_str = f", город = {inn_data['city_invoice']}" if len(inn_data['city_invoice']) > 0 else ""
    comment = (
        "массаж"
        if inn_data['source_invoice'] == "РМ"
        else ("Александрит" if inn_data['source_invoice'] == "АЛЭ" else "нет")
    )
    nds = int(inn_data['new_invoice_amount'] * 5 / 105 * 100) / 100
    payment_details = (
        f"минимальный депозит = {float_rus_format(inn_data['deposit_min_value'])}\n"
        f"средний депозит = {float_rus_format(inn_data['deposit_average_value'])}\n\n"
        f"стоимость лидов = {float_rus_format(inn_data['interval_sale'])}\n"
        f"сумма счетов = {float_rus_format(max(inn_data['interval_invoice'], inn_data['interval_receipt']))}\n"
        f"корректировка = {float_rus_format(inn_data['interval_correction'])}\n"
        f"итого остаток = {float_rus_format(inn_data['interval_invoices_minus_leads'])}"
    ) if inn_data['payment_type'] == "депозит" else (
        f"количество лидов = {float_rus_format(inn_data['interval_cnt'])}\n"
        f"стоимость лидов = {float_rus_format(inn_data['interval_sale'])}\n"
        f"цена лида = {float_rus_format(inn_data['interval_sale'] / inn_data['interval_cnt'] if inn_data['interval_cnt'] != 0 else 0)}\n"
    )

    msg = (
        f"<b>Ответственный = {project}</b>\n\n"
        f"<b>'{inn_data['legal_entity']}'</b>\n"
        f"<b>{project_comment}</b>"
        f"(ИНН = {inn_data['inn']}{city_str}, комментарий = '{comment}')\n\n"
        f"Счет : {float_rus_format(inn_data['new_invoice_amount'])} руб. (НДС = {float_rus_format(nds)})\n\n"
        f"<i>детализация расчетов:</i>\n\n"
        f"{payment_details}"
    )

    send_telegram_message(chat_id=BOT_CHAT_ID_3, message=msg, topic_id=CHAT_3_TOPIC_NEW_INVOICES)

    invoice_output[inn_data['inn']] = create_invoice(
        scloud_base=scloud_base,
        scloud_login=scloud_login,
        scloud_password=scloud_password,
        inn_data=inn_data
    )

    sys_sleep(5)