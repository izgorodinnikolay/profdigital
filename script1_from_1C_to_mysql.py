import os
from dotenv import load_dotenv
from func_import_data_from_1c import get_1с_data_with_retry, nomenclature_text_gr, export_df_to_db_with_retry

def run_script_from_1C_to_mysql():

    load_dotenv(r'C:\Users\user\Desktop\Maks\projects\invoices_2026_07_26\variables.env')

    ########################################################################################################################
    # VARIABLES

    # 1C
    SCLOUD_LOGIN = os.getenv("SCLOUD_LOGIN")
    SCLOUD_PASSWORD = os.getenv("SCLOUD_PASSWORD")
    SCLOUD_BASE = os.getenv("SCLOUD_BASE")

    # MySQL
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = int(os.getenv("DB_PORT"))
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_DBNAME = os.getenv("DB_DBNAME")


    ########################################################################################################################
    DOCUMENT = 'Document_СчетНаОплатуПокупателю'
    DICT_COLUMNS = {
        'Ref_Key': ['invoice_id', 'string'],
        'Number': ['invoice_number', 'string'],
        'ВидОперации': ['invoice_type', 'string'],
        'Date': ['invoice_dt', 'datetime'],
        'Posted': ['is_posted', 'boolean'],
        'Организация_Key': ['organization_id', 'string'],
        'Контрагент_Key': ['partner_id', 'string'],
        'ДоговорКонтрагента_Key': ['contract_id', 'string'],
        'СтруктурнаяЕдиница_Key': ['account_id', 'string'],
        'СуммаДокумента': ['invoice_amount', 'float'],
        'ВалютаДокумента_Key': ['currency_id', 'string'],
        'DeletionMark': ['is_deleted', 'boolean'],
        'Товары': ['service_name', 'list'],
        'Комментарий': ['invoice_comment', 'string'],
        'ОрганизацияПолучатель_Key': ['recipient_key', 'string'],
        'ДополнительныеУсловия_Key': ['additional_terms', 'string'],
        'Ответственный_Key': ['user_key', 'string'],
        'Руководитель_Key': ['manager_key', 'string'],
        'УдалитьУчитыватьНДС': ['vat_flag', 'boolean'],
        'СпособДоставки_Key': ['delivery_method_key', 'string'],
        'ВариантПечатиQRКода': ['print_qr', 'string']
    }
    EXPLODE_COLUMN = 'service_name'
    DICT_EXPLODE_COLUMNS = {
        # 'Ref_Key':['child_invoice_id', 'string'],
        'LineNumber': ['row_num', 'int'],
        'Номенклатура': ['nomenclature', 'string'],
        # 'Номенклатура_Type':'nomenclature_type',
        'Содержание': ['nomenclature_text', 'string'],
        'Количество': ['quantity', 'int'],
        'Цена': ['price', 'float'],
        'Сумма': ['amount', 'float'],
        'ПроцентСкидки': ['discount_percent', 'float'],
        'СуммаСкидки': ['discount_amount', 'float'],
        'СтавкаНДС': ['vat_rate', 'string'],
        'СуммаНДС': ['vat_amount', 'float'],
        # 'КлючКалькуляцииРасходов',
        # 'ВидЛьготыПоТуристическомуНалогу',
        'ИдентификаторСтроки': ['row_id', 'string'],
        'ИдентификаторРодительскойСтроки': ['parent_row_id', 'string']
    }


    df_invoices, df_invoices_detailed = get_1с_data_with_retry(
        scloud_base=SCLOUD_BASE,
        scloud_user=SCLOUD_LOGIN,
        scloud_password=SCLOUD_PASSWORD,
        document=DOCUMENT,
        dict_columns=DICT_COLUMNS,
        explode_column=EXPLODE_COLUMN,
        dict_explode_columns=DICT_EXPLODE_COLUMNS,
        dttm_from_export='',
        status_db_user=DB_USER,
        status_db_password=DB_PASSWORD,
        status_db_host=DB_HOST,
        status_db_port=DB_PORT,
        status_db_dbname=DB_DBNAME,
        status_db_table='status_1c',
    )

    export_df_to_db_with_retry(
        df_src=df_invoices,
        db_user=DB_USER,
        db_password=DB_PASSWORD,
        db_host=DB_HOST,
        db_port=DB_PORT,
        db_dbname=DB_DBNAME,
        db_table='invoice_1c',
        truncate=True
    )

    df_invoices_detailed['nomenclature_text_gr'] = [*map(nomenclature_text_gr, df_invoices_detailed.nomenclature_text)]
    export_df_to_db_with_retry(
        df_src=df_invoices_detailed,
        db_user=DB_USER,
        db_password=DB_PASSWORD,
        db_host=DB_HOST,
        db_port=DB_PORT,
        db_dbname=DB_DBNAME,
        db_table='invoice_detailed_1c',
        truncate=True
    )

    ########################################################################################################################
    DOCUMENT = 'Document_ПоступлениеНаРасчетныйСчет'
    DICT_COLUMNS = {
        'Ref_Key': ['receipt_id', 'string'],
        # 'DataVersion',
        'DeletionMark': ['is_deleted', 'boolean'],
        'Number': ['receipt_number', 'string'],
        'Date': ['receipt_dt', 'datetime'],
        'Posted': ['is_posted', 'boolean'],
        'Организация_Key': ['organization_id', 'string'],
        'ВидОперации': ['receipt_type', 'string'],
        'СчетОрганизации_Key': ['account_id', 'string'],
        # 'ПодразделениеОрганизации_Key',
        # 'СчетБанк_Key',
        'НомерВходящегоДокумента': ['incoming_document_number', 'int'],
        'ДатаВходящегоДокумента': ['incoming_document_date', 'datetime'],
        'Контрагент': ['partner_id', 'string'],
        # 'Контрагент_Type',
        'СчетКонтрагента_Key': ['partner_account_id', 'string'],
        # 'Патент_Key',
        'СуммаДокумента': ['receipt_amount', 'float'],
        # 'СчетУчетаРасчетовСКонтрагентом_Key', 'СубконтоКт1', 'СубконтоКт1_Type', 'СубконтоКт2', 'СубконтоКт2_Type', 'СубконтоКт3', 'СубконтоКт3_Type', 'ПодразделениеКт_Key',
        # 'СтатьяДвиженияДенежныхСредств_Key', 'УдалитьФизЛицо_Key', 'СуммаУслуг', 'КурсНаДатуПриобретенияРеализацииВалюты', 'ОтражатьРазницуВКурсеВСоставеОперационныхРасходов',
        'НазначениеПлатежа': ['purpose_payment', 'string'],
        # 'Ответственный_Key',
        'Комментарий': ['comment', 'string'],
        'ДоговорКонтрагента_Key': ['partner_contract_id', 'string'],
        # 'ВалютаДокумента_Key', 'ДокументОснование', 'ДокументОснование_Type', 'Содержание_УСН', 'Графа4_УСН', 'Графа5_УСН','Графа6_УСН', 'Графа7_УСН', 'ДоходыЕНВД_УСН', 'УдалитьРасходыЕНВД_УСН',
        # 'НДС_УСН', 'РучнаяКорректировка', 'УдалитьПорядокОтраженияАванса', 'УдалитьРучнаяНастройка_УСН', 'БезЗакрывающихДокументов','ДанныеАвтозаполнения', 'ИзмененияАвтозаполнения',
        # 'НомерЧекаККМ', 'УдалитьУслугаНПД_Key', 'ОтражениеВУСН',
        'СуммаВозврата': ['refund_amount', 'float'],
        # 'ИсточникРазметкиАУСН', 'Налог_Key', 'КодВалютнойОперации',
        'РасшифровкаПлатежа': ['decryption_payment', 'list'],
        # 'РеквизитыКонтрагента', 'РазметкаАУСНБанка', 'Организация@navigationLinkUrl', 'СчетОрганизации@navigationLinkUrl', 'СчетБанк@navigationLinkUrl', 'СчетКонтрагента@navigationLinkUrl',
        # 'СчетУчетаРасчетовСКонтрагентом@navigationLinkUrl', 'СтатьяДвиженияДенежныхСредств@navigationLinkUrl', 'Ответственный@navigationLinkUrl', 'ДоговорКонтрагента@navigationLinkUrl',
        # 'ВалютаДокумента@navigationLinkUrl', 'Патент@navigationLinkUrl', 'Налог@navigationLinkUrl'
    }
    EXPLODE_COLUMN = 'decryption_payment'
    DICT_EXPLODE_COLUMNS = {
        'Ref_Key': ['child_receipt_id', 'string'],
        'LineNumber': ['row_number', 'int'],
        'ДоговорКонтрагента_Key': ['contract_id', 'string'],
        'СпособПогашенияЗадолженности': ['repayment method', 'string'],
        'Сделка': ['transaction', 'string'],
        'Сделка_Type': ['transaction_type', 'string'],
        'СуммаПлатежа': ['receipt_amount', 'float'],
        # 'КурсВзаиморасчетов',
        'СуммаВзаиморасчетов': ['settlement_amount', 'float'],
        'СтавкаНДС': ['vat_rate', 'string'],
        'СуммаНДС': ['vat_amount', 'float'],
        'СчетНаОплату_Key': ['invoice_id', 'string'],
        'СтатьяДвиженияДенежныхСредств_Key': ['tmp', 'string'],
        # 'СчетУчетаРасчетовСКонтрагентом_Key', 'СчетУчетаРасчетовПоАвансам_Key', 'СубконтоКт1',
        # 'СубконтоКт1_Type', 'СубконтоКт2', 'СубконтоКт2_Type', 'СубконтоКт3', 'СубконтоКт3_Type', 'ПодразделениеКт_Key','КратностьВзаиморасчетов',
        'СуммаУслуг': ['services_amount', 'float'],
        # 'КурсНаДатуПриобретенияРеализацииВалюты', 'ПорядокОтраженияАванса', 'ПорядокОтраженияАванса_Type',
        'ДоходыУСН': ['sts_income', 'float'],
        # 'УслугаНПД_Key',
        'СуммаВозврата': ['refund_amount', 'float'],
    }

    df_receipts, df_receipts_detailed = get_1с_data_with_retry(
        scloud_base=SCLOUD_BASE,
        scloud_user=SCLOUD_LOGIN,
        scloud_password=SCLOUD_PASSWORD,
        document=DOCUMENT,
        dict_columns=DICT_COLUMNS,
        explode_column=EXPLODE_COLUMN,
        dict_explode_columns=DICT_EXPLODE_COLUMNS,
        status_db_user=DB_USER,
        status_db_password=DB_PASSWORD,
        status_db_host=DB_HOST,
        status_db_port=DB_PORT,
        status_db_dbname=DB_DBNAME,
        status_db_table='status_1c',
    )

    export_df_to_db_with_retry(
        df_src=df_receipts,
        db_user=DB_USER,
        db_password=DB_PASSWORD,
        db_host=DB_HOST,
        db_port=DB_PORT,
        db_dbname=DB_DBNAME,
        db_table='receipts_1c',
        truncate=True
    )

    export_df_to_db_with_retry(
        df_src=df_receipts_detailed,
        db_user=DB_USER,
        db_password=DB_PASSWORD,
        db_host=DB_HOST,
        db_port=DB_PORT,
        db_dbname=DB_DBNAME,
        db_table='receipts_detailed_1c',
        truncate=True
    )


    ########################################################################################################################
    DOCUMENT = 'Document_СписаниеСРасчетногоСчета'
    DICT_COLUMNS = {
        'Ref_Key': ['payment_id', 'string'],
        'DeletionMark': ['is_deleted', 'boolean'],
        'Number': ['payment_number', 'string'],
        'Date': ['payment_dt', 'datetime'],
        'Posted': ['is_posted', 'boolean'],
        'ВидОперации': ['operation_type', 'string'],
        'ВидНалоговогоОбязательства': ['payment_tax_type', 'string'],
        'Организация_Key': ['organization_id', 'string'],
        'СчетОрганизации_Key': ['organization_account_id', 'string'],
        'НомерВходящегоДокумента': ['incoming_document_number', 'string'],
        'ДатаВходящегоДокумента': ['incoming_document_dt', 'datetime'],
        'Контрагент': ['partner_id', 'string'],
        'СчетКонтрагента_Key': ['partner_account_id', 'string'],
        'СуммаДокумента': ['amount', 'float'],
        'СтатьяДвиженияДенежныхСредств_Key': ['cash_flow_article_id', 'string'],
        'НазначениеПлатежа': ['payment_purpose', 'string'],
        'Ответственный_Key': ['responsible_id', 'string'],
        'Комментарий': ['comment', 'string'],
        'ДокументОснование': ['document', 'string'],
        'ДокументОснование_Type': ['document_type', 'string'],
        'ДоговорКонтрагента_Key': ['partner_contract_id', 'string'],
        'Содержание_УСН': ['sts_content', 'string'],
        'НДС_УСН': ['sts_vat', 'float'],
        'РасшифровкаПлатежа': ['payment_description', 'list']
    }
    EXPLODE_COLUMN = 'payment_description'
    DICT_EXPLODE_COLUMNS = {
        'Ref_Key': ['child_payment_id', 'string'],
        'LineNumber': ['row_num', 'int'],
        'ДоговорКонтрагента_Key': ['partner_contract_id', 'string'],
        'СпособПогашенияЗадолженности': ['debt_repayment_method', 'string'],
        'Сделка': ['deal', 'string'],
        # 'Сделка_Type':['deal_type','string'],
        'СуммаПлатежа': ['payment_amount', 'float'],
        'КурсВзаиморасчетов': ['mutual_settlement_rate', 'float'],
        'СуммаВзаиморасчетов': ['mutual_settlement_amount', 'float'],
        'СтавкаНДС': ['vat_rate', 'string'],
        'СуммаНДС': ['vat_amount', 'float'],
        'СтатьяДвиженияДенежныхСредств_Key': ['cash_flow_article_id', 'string'],
        'СчетУчетаРасчетовСКонтрагентом_Key': ['account_id', 'string'],
        'СчетУчетаРасчетовПоАвансам_Key': ['accounting_for_advances_id', 'string'],
        'КратностьВзаиморасчетов': ['mutual_settlements_multiplicity', 'string'],
        'РасходыУСН': ['sts_expenses', 'float'],
        'НДСУСН': ['vat_sts', 'float'],
        'СчетНаОплату_Key': ['invoice_id', 'string'],
        'ВидПлатежаПоКредитамЗаймам': ['payment_for_loans_type', 'string'],
        'ПорядокОтраженияДохода': ['income_reflection_procedure', 'string'],
        'ПорядокОтраженияДохода_Type': ['income_reflection_procedure_type', 'string'],
        'ОтражениеВУСН': ['sts_description', 'string'],
    }

    df_payments, df_payments_detailed = get_1с_data_with_retry(
        scloud_base=SCLOUD_BASE,
        scloud_user=SCLOUD_LOGIN,
        scloud_password=SCLOUD_PASSWORD,
        document=DOCUMENT,
        dict_columns=DICT_COLUMNS,
        explode_column=EXPLODE_COLUMN,
        dict_explode_columns=DICT_EXPLODE_COLUMNS,
        dttm_from_export='',  # DTTM_FROM_EXPORT
        status_db_user=DB_USER,
        status_db_password=DB_PASSWORD,
        status_db_host=DB_HOST,
        status_db_port=DB_PORT,
        status_db_dbname=DB_DBNAME,
        status_db_table='status_1c',
    )

    export_df_to_db_with_retry(
        df_src=df_payments,
        db_user=DB_USER,
        db_password=DB_PASSWORD,
        db_host=DB_HOST,
        db_port=DB_PORT,
        db_dbname=DB_DBNAME,
        db_table='payments_1c',
        truncate=True
    )

    export_df_to_db_with_retry(
        df_src=df_payments_detailed,
        db_user=DB_USER,
        db_password=DB_PASSWORD,
        db_host=DB_HOST,
        db_port=DB_PORT,
        db_dbname=DB_DBNAME,
        db_table='payments_detailed_1c',
        truncate=True
    )


    ########################################################################################################################
    DOCUMENT = 'Catalog_Организации'
    DICT_COLUMNS = {
        'Ref_Key': ['organization_id', 'string'],
        # 'DataVersion':'',
        'DeletionMark': ['is_deleted', 'boolean'],
        'Code': ['organization_number', 'string'],
        'Description': ['organization_name', 'string'],
        # 'ВидОбменаСКонтролирующимиОрганами':'',
        # 'ВидОбменаСКонтролирующимиОрганами_Type':'',
        'ГоловнаяОрганизация_Key': ['parent_organization_id', 'string'],
        # 'КПП':'', 'КодНалоговогоОргана':'',
        'ИНН': ['organization_inn', 'string'],
        # 'ДополнительныйКодФСС':'', 'ЕстьОбособленныеПодразделения':''
        'ИндивидуальныйПредприниматель_Key': ['manager_key', 'string'],
        # 'ДатаРегистрации':'', 'КодНалоговогоОрганаПолучателя':'',
        # 'СвидетельствоНаименованиеОргана':'', 'СвидетельствоКодОргана':'', 'ОсновнойБанковскийСчет_Key':'', 'КодОрганаПФР':'', 'УдалитьКодПоОКАТО':'', 'КодОрганаФСГС':'',
        # 'КодПоОКПО':'', 'НаименованиеНалоговогоОргана':'', 'КодПодчиненностиФСС':'', 'ИПРегистрационныйНомерПФР':'', 'КрупнейшийНалогоплательщик':'', 'КрупнейшийНалогоплательщикКПП':'',
        # 'КрупнейшийНалогоплательщикНаименованиеНалоговогоОргана':'', 'НаименованиеПолное':'', 'НаименованиеСокращенное':'', 'РегистрационныйНомерТФОМС':'', 'ИПРегистрационныйНомерТФОМС':'',
        # 'НаименованиеТерриториальногоОрганаПФР':'', 'НаименованиеТерриториальногоОрганаФСС':'', 'ИПРегистрационныйНомерФСС':'', 'УдалитьИПКодПодчиненностиФСС':'',
        # 'ОбменКаталогОтправкиДанныхОтчетности':'', 'ОбменКаталогПрограммыЭлектроннойПочты':'', 'КодОКОНХ':'', 'ОбменКодАбонента':'', 'ОбособленноеПодразделение':'',
        # 'ПрефиксБП20':'', 'ОГРН':'', 'ПрименятьРайонныйКоэффициент':'', 'ПрименятьСевернуюНадбавку':'', 'РайонныйКоэффициент':'', 'ИностраннаяОрганизация':'',
        # 'НаименованиеИнострОрганизации':'', 'СтранаРегистрации_Key':'', 'КодВСтранеРегистрации':'', 'СтранаПостоянногоМестонахождения_Key':'', 'Префикс':'', 'РегистрационныйНомерФСС':'',
        # 'РегистрацияВНалоговомОргане_Key':'', 'КрупнейшийНалогоплательщикРегистрацияВНалоговомОргане_Key':'', 'УдалитьТерриториальныеУсловияПФР_Key':'', 'РегистрационныйНомерПФР':'',
        # 'ВариантНаименованияДляПечатныхФорм':'', 'НаименованиеПлательщикаПриПеречисленииВБюджет':'', 'СвидетельствоДатаВыдачи':'', 'СвидетельствоСерияНомер':'', 'УчетнаяЗаписьОбмена':'',
        # 'УчетнаяЗаписьОбмена_Type':'', 'КодОКВЭД':'', 'ЦифровойИндексОбособленногоПодразделения':'', 'НаименованиеОКВЭД':'', 'КодОКВЭД2':'', 'НаименованиеОКВЭД2':'',
        # 'ТерриториальныеУсловияПФР_Key':'', 'КодОКОПФ':'', 'НаименованиеОКОПФ':'', 'ВидСтавокЕСНиПФР':'', 'УдалитьЮрФизЛицо':'', 'УдалитьКодИФНС':'', 'КодОКФС':'', 'ФайлЛоготип_Key':'',
        # 'ФайлФаксимильнаяПечать_Key':'', 'ФайлПечать_Key':'', 'УдалитьФайлПодписьРуководителя_Key':'', 'УдалитьФайлПодписьГлавногоБухгалтера_Key':'', 'УдалитьРайонныйКоэффициентРФ':'',
        # 'УдалитьФайлЛоготип_Key':'', 'УдалитьФайлФаксимильнаяПечать_Key':'', 'УдалитьИПИспользуетТрудНаемныхРаботников':'', 'РайонныйКоэффициентРФ':'', 'ДополнительныеУсловияПоУмолчанию_Key':'',
        # 'НекредитнаяФинансоваяОрганизация':'', 'КодОсновногоВидаДеятельностиНФО':'', 'КодИныхВидовДеятельностиНФО':'', 'НаименованиеОсновногоВидаДеятельностиНФО':'',
        # 'НаименованиеИныхВидовДеятельностиНФО':'', 'УдалитьФайлПечать_Key':'', 'УдалитьУдалитьФайлПодписьРуководителя_Key':'', 'УдалитьУдалитьФайлПодписьГлавногоБухгалтера_Key':'',
        # 'ФамилияИП':'', 'ИмяИП':'', 'ОтчествоИП':'', 'НаименованиеОКФС':'', 'ЮридическоеФизическоеЛицо':'', 'УдалитьGLN':'', 'ДополнительныеКодыОКВЭД2':'', 'НаименованиеРегистрирующегоОргана':'',
        # 'НеЗаполнятьПодразделенияВМероприятияхТрудовойДеятельности':'', 'СтатусФизическогоЛица':'', 'ДатаЗакрытия':'', 'РегистрационныйНомерСФР':'', 'ИПРегистрационныйНомерСФР':'',
        # 'ВАрхиве':'', 'ЗаголовокСчетаПоУмолчанию_Key':'', 'КатегорияСтрахователяФизическогоЛица':'', 'КонтактнаяИнформация':'', 'ДополнительныеРеквизиты':'', 'ИсторияНаименований':'',
        # 'ИсторияКонтактнойИнформации':'', 'ИсторияСтатусовФизическогоЛица':'', 'Predefined':'', 'PredefinedDataName':'', 'ГоловнаяОрганизация@navigationLinkUrl':'',
        # 'ИндивидуальныйПредприниматель@navigationLinkUrl':'', 'ОсновнойБанковскийСчет@navigationLinkUrl':'', 'РегистрацияВНалоговомОргане@navigationLinkUrl':'', 'ДополнительныеУсловияПоУмолчанию@navigationLinkUrl':'',
    }

    df_organizations, df_null = get_1с_data_with_retry(
        scloud_base=SCLOUD_BASE,
        scloud_user=SCLOUD_LOGIN,
        scloud_password=SCLOUD_PASSWORD,
        document=DOCUMENT,
        dict_columns=DICT_COLUMNS,
        status_db_user=DB_USER,
        status_db_password=DB_PASSWORD,
        status_db_host=DB_HOST,
        status_db_port=DB_PORT,
        status_db_dbname=DB_DBNAME,
        status_db_table='status_1c',
    )

    export_df_to_db_with_retry(
        df_src=df_organizations,
        db_user=DB_USER,
        db_password=DB_PASSWORD,
        db_host=DB_HOST,
        db_port=DB_PORT,
        db_dbname=DB_DBNAME,
        db_table='organizations_1c',
        truncate=True
    )

    ########################################################################################################################
    DOCUMENT = 'Catalog_Контрагенты'  # полезно - инфо по ИНН для выставления счетов - контрагенты
    DICT_COLUMNS = {
        'Ref_Key': ['partner_id', 'string'],
        # 'DataVersion':'',
        'DeletionMark': ['is_deleted', 'boolean'],
        # 'Parent_Key':'',
        'IsFolder': ['is_folder', 'boolean'],
        'Code': ['partner_number', 'string'],
        'Description': ['partner_name', 'string'],
        'НаименованиеПолное': ['partner_full_name', 'string'],
        # 'ОбособленноеПодразделение':'',
        'ЮридическоеФизическоеЛицо': ['partner_type', 'string'],
        # 'СтранаРегистрации_Key':'', 'ГоловнойКонтрагент_Key':'',
        'ИНН': ['partner_inn', 'string'],
        # 'КПП':'', 'КодПоОКПО':'', 'ДокументУдостоверяющийЛичность':'', 'ОсновнойБанковскийСчет_Key':'', 'УдалитьОсновнойДоговорКонтрагента_Key':'', 'ОсновноеКонтактноеЛицо_Key':'', 'Комментарий':'',
        # 'ДополнительнаяИнформация':'', 'УдалитьЮрФизЛицо':'',
        'ИННВведенКорректно': ['inn_is_correct', 'boolean'],
        # 'КППВведенКорректно':'', 'РасширенноеПредставлениеИНН':'', 'РасширенноеПредставлениеКПП':'', 'НалоговыйНомер':'', 'РегистрационныйНомер':'', 'ГосударственныйОрган':'',
        # 'ВидГосударственногоОргана':'', 'КодГосударственногоОргана':'', 'СвидетельствоСерияНомер':'', 'СвидетельствоДатаВыдачи':'', 'ДатаРегистрации':'', 'ДатаСоздания':'',
        # 'УдалитьСамозанятый':'', 'ИндивидуальныйПредприниматель':'', 'НаименованиеНерезидентаРус':'', 'Ответственный_Key':'', 'КодОКАТОДляТаможни':'', 'КонтактнаяИнформация':'',
        # 'ДополнительныеРеквизиты':'', 'ИсторияКПП':'', 'ИсторияНаименований':'', 'ИсторияКонтактнойИнформации':'', 'Predefined':'', 'PredefinedDataName':'', 'СтранаРегистрации@navigationLinkUrl':'',
        # 'ГоловнойКонтрагент@navigationLinkUrl':'', 'ОсновнойБанковскийСчет@navigationLinkUrl':'', 'ОсновноеКонтактноеЛицо@navigationLinkUrl':'', 'Parent@navigationLinkUrl':'',
    }
    DB_TABLE = 'partners_1c'

    df_partners, df_null = get_1с_data_with_retry(
        scloud_base=SCLOUD_BASE,
        scloud_user=SCLOUD_LOGIN,
        scloud_password=SCLOUD_PASSWORD,
        document=DOCUMENT,
        dict_columns=DICT_COLUMNS,
        status_db_user=DB_USER,
        status_db_password=DB_PASSWORD,
        status_db_host=DB_HOST,
        status_db_port=DB_PORT,
        status_db_dbname=DB_DBNAME,
        status_db_table='status_1c',
    )

    export_df_to_db_with_retry(
        df_src=df_partners,
        db_user=DB_USER,
        db_password=DB_PASSWORD,
        db_host=DB_HOST,
        db_port=DB_PORT,
        db_dbname=DB_DBNAME,
        db_table=DB_TABLE,
        truncate=True
    )

    ########################################################################################################################
    DOCUMENT = 'Catalog_БанковскиеСчета'  #
    DICT_COLUMNS = {
        'Ref_Key': ['account_id', 'string'],
        # 'DataVersion':'',
        'DeletionMark': ['is_deleted', 'boolean'],
        'Owner': ['owner_id', 'string'],
        'Owner_Type': ['owner_id_ref', 'string'],
        'Code': ['account_num', 'string'],
        'Description': ['description', 'string'],
        'НомерСчета': ['account_number', 'string'],
        'Банк_Key': ['bank_id', 'string'],
        'Валютный': ['foreign_flg', 'boolean'],
        'ВалютаДенежныхСредств_Key': ['currency_id', 'string'],
        'ВидСчета': ['account_type', 'string'],
        'ТекстКорреспондента': ['description_2', 'string'],
    }
    DB_TABLE = 'account_1c'

    df_accounts, df_null = get_1с_data_with_retry(
        scloud_base=SCLOUD_BASE,
        scloud_user=SCLOUD_LOGIN,
        scloud_password=SCLOUD_PASSWORD,
        document=DOCUMENT,
        dict_columns=DICT_COLUMNS,
        status_db_user=DB_USER,
        status_db_password=DB_PASSWORD,
        status_db_host=DB_HOST,
        status_db_port=DB_PORT,
        status_db_dbname=DB_DBNAME,
        status_db_table='status_1c',
    )

    export_df_to_db_with_retry(
        df_src=df_accounts,
        db_user=DB_USER,
        db_password=DB_PASSWORD,
        db_host=DB_HOST,
        db_port=DB_PORT,
        db_dbname=DB_DBNAME,
        db_table=DB_TABLE,
        truncate=True
    )


    ########################################################################################################################
    DOCUMENT = 'Catalog_ДоговорыКонтрагентов'  #
    DICT_COLUMNS = {
        'Ref_Key': ['contract_id', 'string'],
        # 'DataVersion':'',
        'DeletionMark': ['is_deleted', 'boolean'],
        'Owner_Key': ['partner_id', 'string'],
        'Code': ['contract_number', 'string'],
        'Description': ['description', 'string'],
        'ВалютаВзаиморасчетов_Key': ['currency_id', 'string'],
        'Комментарий': ['comment', 'string'],
        'Организация_Key': ['organization_id', 'string'],
        'ВидДоговора': ['contract_type', 'string'],
        'Руководитель_Key': ['manager_id', 'string'],
        'РуководительКонтрагента': ['partner_manager', 'string'],
        'СпособЗаполненияСтавкиНДС': ['vat_type', 'string'],
        'СтавкаНДС': ['vat', 'string']
    }
    DB_TABLE = 'contract_1c'

    df_contracts, df_null = get_1с_data_with_retry(
        scloud_base=SCLOUD_BASE,
        scloud_user=SCLOUD_LOGIN,
        scloud_password=SCLOUD_PASSWORD,
        document=DOCUMENT,
        dict_columns=DICT_COLUMNS,
        status_db_user=DB_USER,
        status_db_password=DB_PASSWORD,
        status_db_host=DB_HOST,
        status_db_port=DB_PORT,
        status_db_dbname=DB_DBNAME,
        status_db_table='status_1c',
    )

    export_df_to_db_with_retry(
        df_src=df_contracts,
        db_user=DB_USER,
        db_password=DB_PASSWORD,
        db_host=DB_HOST,
        db_port=DB_PORT,
        db_dbname=DB_DBNAME,
        db_table=DB_TABLE,
        truncate=True
    )

    ########################################################################################################################
    DOCUMENT = 'Catalog_СтатьиДвиженияДенежныхСредств'
    DICT_COLUMNS = {
        'Ref_Key': ['cash_flow_article_id', 'string'],
        'DeletionMark': ['is_deleted', 'boolean'],
        'IsFolder': ['is_folder', 'boolean'],
        'Code': ['cash_flow_article_number', 'string'],
        'Description': ['description', 'string'],
        'ВидДвиженияДенежныхСредств': ['cash_flow_article_type', 'string'],
        'Комментарий': ['comment', 'string'],
        'PredefinedDataName': ['predefined_data_name', 'string'],
    }
    DB_TABLE = 'cash_flow_article_1c'

    df_cash_flow_article, df_null = get_1с_data_with_retry(
        scloud_base=SCLOUD_BASE,
        scloud_user=SCLOUD_LOGIN,
        scloud_password=SCLOUD_PASSWORD,
        document=DOCUMENT,
        dict_columns=DICT_COLUMNS,
        status_db_user=DB_USER,
        status_db_password=DB_PASSWORD,
        status_db_host=DB_HOST,
        status_db_port=DB_PORT,
        status_db_dbname=DB_DBNAME,
        status_db_table='status_1c',
    )

    export_df_to_db_with_retry(
        df_src=df_cash_flow_article,
        db_user=DB_USER,
        db_password=DB_PASSWORD,
        db_host=DB_HOST,
        db_port=DB_PORT,
        db_dbname=DB_DBNAME,
        db_table=DB_TABLE,
        truncate=True
    )


    ########################################################################################################################
    DOCUMENT = 'Catalog_Пользователи'
    DICT_COLUMNS = {
        'Ref_Key': ['cash_flow_article_id', 'string'],
        'DeletionMark': ['is_deleted', 'boolean'],
        'Description': ['description', 'string'],
        'Недействителен': ['is_unavailable', 'boolean'],
        'Служебный': ['is_service', 'boolean'],
        'Подготовлен': ['is_prepared', 'boolean'],
    }
    DB_TABLE = 'users_1c'

    df_users, df_null = get_1с_data_with_retry(
        scloud_base=SCLOUD_BASE,
        scloud_user=SCLOUD_LOGIN,
        scloud_password=SCLOUD_PASSWORD,
        document=DOCUMENT,
        dict_columns=DICT_COLUMNS,
        status_db_user=DB_USER,
        status_db_password=DB_PASSWORD,
        status_db_host=DB_HOST,
        status_db_port=DB_PORT,
        status_db_dbname=DB_DBNAME,
        status_db_table='status_1c',
    )

    export_df_to_db_with_retry(
        df_src=df_users,
        db_user=DB_USER,
        db_password=DB_PASSWORD,
        db_host=DB_HOST,
        db_port=DB_PORT,
        db_dbname=DB_DBNAME,
        db_table=DB_TABLE,
        truncate=True
    )


    ########################################################################################################################
    DOCUMENT = 'Catalog_ФизическиеЛица'
    DICT_COLUMNS = {
        'Ref_Key': ['individual_id', 'string'],
        'DeletionMark': ['is_deleted', 'boolean'],
        'IsFolder': ['is_folder', 'boolean'],
        'Code': ['individual_number', 'string'],
        'Description': ['description', 'string'],
        'ИНН': ['inn', 'string'],
        'ФИО': ['full_name', 'string']
    }
    DB_TABLE = 'individuals_1c'

    df_individuals, df_null = get_1с_data_with_retry(
        scloud_base=SCLOUD_BASE,
        scloud_user=SCLOUD_LOGIN,
        scloud_password=SCLOUD_PASSWORD,
        document=DOCUMENT,
        dict_columns=DICT_COLUMNS,
        status_db_user=DB_USER,
        status_db_password=DB_PASSWORD,
        status_db_host=DB_HOST,
        status_db_port=DB_PORT,
        status_db_dbname=DB_DBNAME,
        status_db_table='status_1c',
    )

    export_df_to_db_with_retry(
        df_src=df_individuals,
        db_user=DB_USER,
        db_password=DB_PASSWORD,
        db_host=DB_HOST,
        db_port=DB_PORT,
        db_dbname=DB_DBNAME,
        db_table=DB_TABLE,
        truncate=True
    )


    ########################################################################################################################