import json
import requests

from datetime import datetime
from requests.auth import HTTPBasicAuth
from time import sleep as sys_sleep

from func_common import send_telegram_message


def create_invoice(scloud_base,
                   scloud_login,
                   scloud_password,
                   payment_type,
                   partner_id,
                   contract_id,
                   organization_id,
                   manager_key,
                   invoice_amount,
                   interval_cnt,
                   interval_sale,
                   source_invoice
                   ):
    document = 'Document_СчетНаОплатуПокупателю'
    url = f'{scloud_base}/{document}'
    headers = {'Authorization': 'Basic', 'Accept': 'application/json'}

    document_data = {
        'Date': datetime.strftime(datetime.now(), '%Y-%m-%dT%H:%M:%S'),
        'Posted': True,

        # из 1С
        'СтруктурнаяЕдиница_Key': '6efcc024-92da-11f0-96c0-00155d46f8c2',  # 40802810200008615630, АО "ТИНЬКОФФ БАНК"
        'Ответственный_Key': 'dcbbf600-1c57-11f1-8778-00155d46fc0e',  # dop0265986

        # Из MySQL
        'Контрагент_Key': partner_id,
        'ДоговорКонтрагента_Key': contract_id,
        'СуммаДокумента': invoice_amount,
        'Организация_Key': organization_id,  # ИП Бушуева Е. Б.
        'ОрганизацияПолучатель_Key': organization_id,  # ИП Бушуева Е. Б.
        'Руководитель_Key': manager_key,  # Бушуева Елена Борисовна
        'Комментарий': 'массаж' if source_invoice == 'РМ' else ('Александрит' if source_invoice == 'АЛЭ' else ''),

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
            'Содержание': 'Оплата стоимости лидов (депозит)' if payment_type == 'депозит' else 'Оплата стоимости лидов',
            'Количество': 0 if payment_type == 'депозит' else interval_cnt,
            'Цена': invoice_amount if payment_type == 'депозит' else round(interval_sale / interval_cnt, 2),
            'Сумма': invoice_amount,
            'ПроцентСкидки': 0,
            'СуммаСкидки': 0,
            'СтавкаНДС': 'НДС5',
            'СуммаНДС': int(invoice_amount * 5 / 105 * 100) / 100}]
    }

    response = requests.post(url, headers=headers, data=json.dumps(document_data),
                             auth=HTTPBasicAuth(scloud_login, scloud_password))

    return response.status_code


def create_invoice_on_1c(scloud_base, scloud_login, scloud_password, df_new_invoices):
    invoice_output = {}

    lead_list = df_new_invoices.to_dict(orient='records')
    for row in lead_list:
        inn = row['inn']
        payment_type = row['payment_type']
        partner_id = row['partner_id']
        contract_id = row['contract_id']
        organization_id = row['organization_id']
        manager_key = row['manager_key']
        invoice_amount = row['new_invoice_amount']
        interval_cnt = row['interval_cnt']
        interval_sale = row['interval_sale']
        source_invoice = row['source_invoice']
        legal_entity = row['legal_entity']
        city_invoice = row['city_invoice']
        interval_invoice = row['interval_invoice']
        interval_receipt = row['interval_receipt']
        interval_correction = row['interval_correction']
        interval_deposit_balance = row['interval_deposit_balance']
        deposit_min_value = row['deposit_min_value']
        deposit_average_value = row['deposit_average_value']

        city_str = f", город = {city_invoice}" if len(city_invoice) > 0 else ""
        comment = (
            "массаж"
            if source_invoice == "РМ"
            else ("Александрит" if source_invoice == "АЛЭ" else "нет")
        )
        nds = int(invoice_amount * 5 / 105 * 100) / 100

        msg = (
            f"*'{legal_entity}'*\n"
            f"(ИНН = {inn}{city_str}, комментарий = '{comment}')\n\n"
            f"Счет : {invoice_amount:_.0f} руб. (НДС = {nds:_.2f})\n\n"
            f"_детализация расчетов:_\n\n"
        ).replace('_', ' ')

        if payment_type == "депозит":
            payment_details = (
                f"минимальный депозит = {deposit_min_value:_.0f}\n"
                f"средний депозит = {deposit_average_value:_.0f}\n\n"
                f"стоимость лидов = {interval_sale:_.0f}\n"
                f"сумма счетов = {max(interval_invoice, interval_receipt):_.0f}\n"
                f"корректировка = {interval_correction:_.0f}\n"
                f"итого остаток = {interval_deposit_balance:_.0f}"
            ).replace('_', ' ')
        else:
            payment_details = (
                f"количество лидов = {interval_cnt:_.0f}\n"
                f"стоимость лидов = {interval_sale:_.0f}\n"
                f"цена лида = {interval_sale / interval_cnt if interval_cnt != 0 else 0:_.2f}\n"
                f"!!! цена лида с учетом тестовых (цена 0 руб.)"
                f"!!! корректировка = {interval_correction:_.0f} - должна быть 0"
            ).replace('_', ' ')

        msg += f"*тип оплаты = {payment_type}*\n\n" + payment_details

        send_telegram_message(message=msg)

        invoice_output[inn] = create_invoice(
            scloud_base=scloud_base,
            scloud_login=scloud_login,
            scloud_password=scloud_password,
            payment_type=payment_type,
            partner_id=partner_id,
            contract_id=contract_id,
            organization_id=organization_id,
            manager_key=manager_key,
            invoice_amount=invoice_amount,
            interval_cnt=interval_cnt,
            interval_sale=interval_sale,
            source_invoice=source_invoice
        )

        sys_sleep(1)

    return invoice_output