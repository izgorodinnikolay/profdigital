import pandas as pd


def update_df_single_column_type(df_in: pd.DataFrame, column_name: str, column_type: str):
    if column_type == 'datetime':
        return df_in[column_name].replace(['0', 0, '0000-00-00', '0000-00-00 00:00:00', ''], pd.NA).apply(pd.to_datetime, utc=True, errors='coerce')
    elif column_type in ['string', 'boolean', 'int', 'float']:
        return df_in[column_name].astype(column_type)
    else:
        return df_in[column_name]


def update_df_all_column_types(df_in: pd.DataFrame, dict_columns: dict):
    for value in dict_columns.values():
        df_in[value[0]] = update_df_single_column_type(df_in=df_in, column_name=value[0], column_type=value[1])
    return df_in


def is_float_string(val):
    try:
        float(val)
        return True
    except ValueError:
        return False


def update_flg_stop(deposit_min_value: str, deposit_average_value: str) -> str:
    return 'на стопе' if deposit_min_value == 'на стопе' or deposit_average_value == 'на стопе' else ''


def update_inn(inn: str, comment: str) -> list:
    inn = inn[0:-2] if inn[-2:len(inn)] == '.0' else inn
    if len(inn) in (9, 11): inn = '0' + inn
    if not is_float_string(inn):
        comment += 'Поле ИНН заполнено некорректно'

    return [inn, comment]


def update_payment_type(payment_type: str, deposit_min_value: str, deposit_average_value: str, comment: str) -> list:
    if payment_type == '?':
        if deposit_min_value == 'постоплата' or deposit_average_value == 'постоплата' or deposit_average_value == 'на стопе':
            payment_type = 'постоплата. еженедельно'
            comment += "Не заполнен Депозит (тип отплаты). Установил 'постоплата. еженедельно'. "
        elif is_float_string(deposit_min_value) and is_float_string(deposit_average_value):
            payment_type = 'депозит'
            comment += "Не заполнен Депозит (тип отплаты). Установил 'депозит'. "
        else:
            payment_type = 'постоплата. еженедельно'
            comment += "Не заполнен Депозит (тип отплаты). Установил 'постоплата. еженедельно'. "
    elif payment_type in ['депозит', 'депозит   ', 'депозит / была постоплата']:
        payment_type = 'депозит'
    elif payment_type in ('постоплата каждый пн за предыдущую неделю', 'оплата с агентских'):
        payment_type = 'постоплата. еженедельно'
    elif payment_type == 'счет 15 и 30 числа\nкаждого месяца':
        payment_type = 'постоплата. 15 и 30'
    elif payment_type == 'постоплата за месяц':
        payment_type = 'постоплата. ежемесячно'
    else:
        payment_type = 'постоплата. еженедельно'
        comment += "Не заполнен Депозит (тип отплаты). Установил 'постоплата. еженедельно'. "

    return [payment_type, comment]


def update_deposit_value(payment_type: str, deposit_min_value: str, deposit_average_value: str, comment: str) -> list:
    if deposit_average_value.find('-') > 0:
        deposit_average_value = deposit_average_value[0:deposit_average_value.find('-')].strip()
        comment += "В поле 'Средний размер депозитов' есть '-'."
    else:
        deposit_average_value = deposit_average_value.strip()

    if payment_type == 'депозит':
        if is_float_string(deposit_min_value):
            deposit_min_value = float(deposit_min_value)
        else:
            deposit_min_value = 5000.0
            comment += "Поле 'Порог остатка' не является числом (поставил 5000). "

        if is_float_string(deposit_average_value):
            deposit_average_value = float(deposit_average_value)
        else:
            deposit_average_value = 20000.0
            comment += "Поле 'Средний размер депозитов' не является числом (поставил 20000). "
    else:
        deposit_min_value, deposit_average_value = 0, 0

    return [deposit_min_value, deposit_average_value, comment]


def get_google_payment_method(google_pm_sheet_id: str, google_pm_gid: str, google_pm_columns: dict) -> pd.DataFrame:
    # загрузим данные по типам счетов из таблицы google
    url = f"https://docs.google.com/spreadsheets/d/{google_pm_sheet_id}/export?format=csv&gid={google_pm_gid}"
    payment_method = pd.read_csv(url)

    # оставим только нужные поля и переименуем
    payment_method = payment_method[google_pm_columns.keys()].rename(
        columns={old_name: new_name[0] for old_name, new_name in google_pm_columns.items()})
    payment_method = update_df_all_column_types(df_in=payment_method, dict_columns=google_pm_columns)

    # протянем тип оплаты (payment_type)
    payment_method['payment_type'] = payment_method['payment_type'].ffill()

    # заменим нулы на '?'
    payment_method = payment_method.fillna('?')

    # добавим поле comment для заполнения инфо по качеству заполнения данных в google-таблице
    payment_method['comment'] = ''

    payment_method['flg_stop'] = [
        *map(update_flg_stop, payment_method.deposit_min_value, payment_method.deposit_average_value)]

    # обновим ИНН, т.к. при конвертации данных из google-таблицы, python добавляет '.0' в конце
    payment_method[['inn', 'comment']] = [*map(update_inn, payment_method.inn, payment_method.comment)]

    # обновим тип платежа (payment_type)
    payment_method[['payment_type', 'comment']] = \
        [*map(update_payment_type,
              payment_method.payment_type,
              payment_method.deposit_min_value,
              payment_method.deposit_average_value,
              payment_method.comment)]

    # обновим deposit_min_value (Порог остатка) и deposit_average_value (Средний размер депозитов)
    payment_method[['deposit_min_value', 'deposit_average_value', 'comment']] = \
        [*map(update_deposit_value,
              payment_method.payment_type,
              payment_method.deposit_min_value,
              payment_method.deposit_average_value,
              payment_method.comment)]

    return payment_method