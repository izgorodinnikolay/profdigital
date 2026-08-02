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
            'Ref_Key':['invoice_id', 'string'],
            'Number':['invoice_number', 'string'],
            'ВидОперации':['invoice_type', 'string'],
            'Date':['invoice_dt', 'datetime'],
            'Posted':['is_posted', 'boolean'],
            'Организация_Key':['organization_id', 'string'],
            'Контрагент_Key':['partner_id', 'string'],
            'ДоговорКонтрагента_Key':['contract_id', 'string'],
            'СуммаДокумента':['invoice_amount', 'float'],
            'DeletionMark':['is_deleted', 'boolean'],
            'Товары':['service_name', 'list'],
            'Комментарий':['invoice_comment', 'string'],
        }
    EXPLODE_COLUMN = 'service_name'
    DICT_EXPLODE_COLUMNS = {
            # 'Ref_Key':['child_invoice_id', 'string'],
            'LineNumber':['row_num', 'int'],
            'Номенклатура':['nomenclature', 'string'],
            # 'Номенклатура_Type':'nomenclature_type',
            'Содержание':['nomenclature_text', 'string'],
            'Количество':['quantity', 'int'],
            'Цена':['price', 'float'],
            'Сумма':['amount', 'float'],
            'ПроцентСкидки':['discount_percent', 'float'],
            'СуммаСкидки':['discount_amount', 'float'],
            'СтавкаНДС':['vat_rate', 'string'],
            'СуммаНДС':['vat_amount', 'float'],
            # 'КлючКалькуляцииРасходов',
            # 'ВидЛьготыПоТуристическомуНалогу',
            'ИдентификаторСтроки':['row_id', 'string'],
            'ИдентификаторРодительскойСтроки':['parent_row_id', 'string']
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
        'Ref_Key':['receipt_id', 'string'],
        # 'DataVersion',
        'DeletionMark':['is_deleted', 'boolean'],
        'Number':['receipt_number', 'string'],
        'Date':['receipt_dt', 'datetime'],
        'Posted':['is_posted', 'boolean'],
        'Организация_Key':['organization_id', 'string'],
        'ВидОперации':['receipt_type', 'string'],
        'СчетОрганизации_Key':['account_id', 'string'],
        # 'ПодразделениеОрганизации_Key',
        # 'СчетБанк_Key',
        'НомерВходящегоДокумента':['incoming_document_number', 'int'],
        'ДатаВходящегоДокумента':['incoming_document_date', 'datetime'],
        'Контрагент':['partner_id', 'string'],
        # 'Контрагент_Type',
        'СчетКонтрагента_Key':['partner_account_id', 'string'],
        # 'Патент_Key',
        'СуммаДокумента':['receipt_amount', 'float'],
        # 'СчетУчетаРасчетовСКонтрагентом_Key', 'СубконтоКт1', 'СубконтоКт1_Type', 'СубконтоКт2', 'СубконтоКт2_Type', 'СубконтоКт3', 'СубконтоКт3_Type', 'ПодразделениеКт_Key',
        # 'СтатьяДвиженияДенежныхСредств_Key', 'УдалитьФизЛицо_Key', 'СуммаУслуг', 'КурсНаДатуПриобретенияРеализацииВалюты', 'ОтражатьРазницуВКурсеВСоставеОперационныхРасходов',
        'НазначениеПлатежа':['purpose_payment', 'string'],
        # 'Ответственный_Key',
        'Комментарий':['comment', 'string'],
        'ДоговорКонтрагента_Key':['partner_contract_id', 'string'],
        # 'ВалютаДокумента_Key', 'ДокументОснование', 'ДокументОснование_Type', 'Содержание_УСН', 'Графа4_УСН', 'Графа5_УСН','Графа6_УСН', 'Графа7_УСН', 'ДоходыЕНВД_УСН', 'УдалитьРасходыЕНВД_УСН',
        # 'НДС_УСН', 'РучнаяКорректировка', 'УдалитьПорядокОтраженияАванса', 'УдалитьРучнаяНастройка_УСН', 'БезЗакрывающихДокументов','ДанныеАвтозаполнения', 'ИзмененияАвтозаполнения',
        # 'НомерЧекаККМ', 'УдалитьУслугаНПД_Key', 'ОтражениеВУСН',
        'СуммаВозврата':['refund_amount', 'float'],
        # 'ИсточникРазметкиАУСН', 'Налог_Key', 'КодВалютнойОперации',
        'РасшифровкаПлатежа':['decryption_payment', 'list'],
        # 'РеквизитыКонтрагента', 'РазметкаАУСНБанка', 'Организация@navigationLinkUrl', 'СчетОрганизации@navigationLinkUrl', 'СчетБанк@navigationLinkUrl', 'СчетКонтрагента@navigationLinkUrl',
        # 'СчетУчетаРасчетовСКонтрагентом@navigationLinkUrl', 'СтатьяДвиженияДенежныхСредств@navigationLinkUrl', 'Ответственный@navigationLinkUrl', 'ДоговорКонтрагента@navigationLinkUrl',
        # 'ВалютаДокумента@navigationLinkUrl', 'Патент@navigationLinkUrl', 'Налог@navigationLinkUrl'
    }
    EXPLODE_COLUMN = 'decryption_payment'
    DICT_EXPLODE_COLUMNS = {
        'Ref_Key':['child_receipt_id', 'string'],
        'LineNumber':['row_number', 'int'],
        'ДоговорКонтрагента_Key':['contract_id', 'string'],
        'СпособПогашенияЗадолженности':['repayment method', 'string'],
        'Сделка':['transaction', 'string'],
        'Сделка_Type':['transaction_type', 'string'],
        'СуммаПлатежа':['receipt_amount', 'float'],
        # 'КурсВзаиморасчетов',
        'СуммаВзаиморасчетов':['settlement_amount', 'float'],
        'СтавкаНДС':['vat_rate', 'string'],
        'СуммаНДС':['vat_amount', 'float'],
        'СчетНаОплату_Key':['invoice_id', 'string'],
        'СтатьяДвиженияДенежныхСредств_Key':['tmp', 'string'],
        # 'СчетУчетаРасчетовСКонтрагентом_Key', 'СчетУчетаРасчетовПоАвансам_Key', 'СубконтоКт1',
        # 'СубконтоКт1_Type', 'СубконтоКт2', 'СубконтоКт2_Type', 'СубконтоКт3', 'СубконтоКт3_Type', 'ПодразделениеКт_Key','КратностьВзаиморасчетов',
        'СуммаУслуг':['services_amount', 'float'],
        # 'КурсНаДатуПриобретенияРеализацииВалюты', 'ПорядокОтраженияАванса', 'ПорядокОтраженияАванса_Type',
        'ДоходыУСН':['sts_income', 'float'],
        # 'УслугаНПД_Key',
        'СуммаВозврата':['refund_amount', 'float'],
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
    DOCUMENT = 'Catalog_Организации'
    DICT_COLUMNS = {
        'Ref_Key':['organization_id', 'string'],
        # 'DataVersion':'',
        'DeletionMark':['is_deleted', 'boolean'],
        'Code':['organization_number', 'string'],
        'Description':['organization_name', 'string'],
        # 'ВидОбменаСКонтролирующимиОрганами':'',
        # 'ВидОбменаСКонтролирующимиОрганами_Type':'',
        'ГоловнаяОрганизация_Key':['parent_organization_id', 'string'],
        # 'КПП':'', 'КодНалоговогоОргана':'',
        'ИНН':['organization_inn', 'string'],
        # 'ДополнительныйКодФСС':'', 'ЕстьОбособленныеПодразделения':'', 'ИндивидуальныйПредприниматель_Key':'', 'ДатаРегистрации':'', 'КодНалоговогоОрганаПолучателя':'',
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
    DOCUMENT = 'Catalog_Контрагенты' # полезно - инфо по ИНН для выставления счетов - контрагенты
    DICT_COLUMNS = {
        'Ref_Key':['partner_id', 'string'],
        # 'DataVersion':'',
        'DeletionMark':['is_deleted', 'boolean'],
        # 'Parent_Key':'',
        'IsFolder':['is_folder', 'boolean'],
        'Code':['partner_number', 'string'],
        'Description':['partner_name', 'string'],
        'НаименованиеПолное':['partner_full_name', 'string'],
        # 'ОбособленноеПодразделение':'',
        'ЮридическоеФизическоеЛицо':['partner_type', 'string'],
        # 'СтранаРегистрации_Key':'', 'ГоловнойКонтрагент_Key':'',
        'ИНН':['partner_inn', 'string'],
        # 'КПП':'', 'КодПоОКПО':'', 'ДокументУдостоверяющийЛичность':'', 'ОсновнойБанковскийСчет_Key':'', 'УдалитьОсновнойДоговорКонтрагента_Key':'', 'ОсновноеКонтактноеЛицо_Key':'', 'Комментарий':'',
        # 'ДополнительнаяИнформация':'', 'УдалитьЮрФизЛицо':'',
        'ИННВведенКорректно':['inn_is_correct', 'boolean'],
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