import datetime
import json
import requests
import time
from requests.auth import HTTPBasicAuth

def create_invoice(scloud_base, scloud_login, scloud_password, partner_id, contract_id, organization_id, manager_key,
                   invoice_amount):
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

        # константы
        'ВалютаДокумента_Key': '9838a908-78df-11e8-80df-0050569f2e9f',
        'ДополнительныеУсловия_Key': 'a077deef-78df-11e8-80df-0050569f2e9f',  # Типовые условия
        'СпособДоставки_Key': '3321a217-b558-11ec-a1c3-00155d46ae10',  # Самовывоз
        'УдалитьУчитыватьНДС': True,  #
        'ВидОперации': 'ТоварыИУслуги',
        'ВариантПечатиQRКода': 'НеПечатать',  # уточнить
        'Товары': [{
            'LineNumber': '1',
            'Номенклатура': '44d84e8c-ab20-11ef-8a67-00155d46f8c3',
            'Номенклатура_Type': 'StandardODATA.Catalog_Номенклатура',
            'Содержание': 'Оплата стоимости лидов (депозит)',
            'Количество': 0,
            'Цена': invoice_amount,
            'Сумма': invoice_amount,
            'ПроцентСкидки': 0,
            'СуммаСкидки': 0,
            'СтавкаНДС': 'БезНДС',
            'СуммаНДС': 0}]
    }

    response = requests.post(url, headers=headers, data=json.dumps(document_data),
                             auth=HTTPBasicAuth(scloud_login, scloud_password))

    return response.status_code


def create_invoice_on_1c(scloud_base, scloud_login, scloud_password, df_new_invoices):
    invoice_output = {}
    if df_new_invoices.shape[0] > 0:
        lead_list = df_new_invoices.to_dict(orient='records')
        for row in lead_list:
            inn = row['inn']
            partner_id = row['partner_id']
            contract_id = row['contract_id']
            organization_id = row['organization_id']
            manager_key = row['manager_key']
            invoice_amount = row['new_invoice_amount']

            invoice_output[inn] = create_invoice(scloud_base, scloud_login, scloud_password, partner_id, contract_id,
                                                 organization_id, manager_key, invoice_amount)

            time.sleep(1)

    return invoice_output