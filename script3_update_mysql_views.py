import os
from dotenv import load_dotenv
from func_update_data_on_mysql import mysql_update_view

def run_script_update_mysql_views():

    load_dotenv(r'C:\Users\user\Desktop\Maks\projects\invoices_2026_07_26\variables.env')

    ########################################################################################################################
    # VARIABLES

    # MySQL
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = int(os.getenv("DB_PORT"))
    DB_DBNAME = os.getenv("DB_DBNAME")
    DB_SUPER_USER = os.getenv("DB_SUPER_USER")
    DB_SUPER_PASSWORD = os.getenv("DB_SUPER_PASSWORD")
    DB_SUPER_DBNAME = os.getenv("DB_SUPER_DBNAME")


    ########################################################################################################################
    TBL_DB = 'j28046070_sandbox'
    TBL_NAME = 'view_leads'
    QUERY = f"""insert into {TBL_DB}.{TBL_NAME}
                select l.project, l.dateAdd, l.dateTimeAdd
                	,DATE_ADD(l.dateAdd, INTERVAL (6 - WEEKDAY(l.dateAdd)) DAY) as week_end
                	,case when l.inn = '720307197077' then '2463115644'
                          when l.inn = '761107378757' then '760212666248'
                          when upper(l.legalentity) like '%%ЮКЛИН%%' then '0274140585'
                		when length(l.inn) in (9, 11) then '0'||l.inn else l.inn end as inn
                	,l.legalEntity, l.source, l.company, l.name, l.phone, l.city
                	,case when l.inn in ('2310229806', '3900034752', '4205421649') then l.city else '' end as city_invoice
                	,l.branch, l.sendStatus, l.sendDateTime, l.purchase, l.sale
                    ,case when row_number() over(partition by l.inn, l.phone, l.source, l.dateAdd - INTERVAL (DAY(l.dateAdd) - 1) DAY order by l.dateTimeAdd) > 1 then 'Дубликат' else '' end as duplicateFlag
                from j28046070_leads.leads as l"""

    mysql_update_view(
        db_user=DB_SUPER_USER,
        db_password=DB_SUPER_PASSWORD,
        db_host=DB_HOST,
        db_port=DB_PORT,
        db_dbname='j28046070_leads',
        tbl_name=TBL_NAME,
        tbl_db=TBL_DB,
        query=QUERY
    )


    ########################################################################################################################
    TBL_DB = 'j28046070_sandbox'
    TBL_NAME = 'view_invoices'
    QUERY = f"""insert into {TBL_DB}.{TBL_NAME}
                with 
                 invoice_nomenclature_rn as (
                	select invoice_id, nomenclature_text_gr, nomenclature_text, row_number() over(partition by invoice_id order by amount desc) as rn 
                	from j28046070_sandbox.invoice_detailed_1c)
                ,invoice_nomenclature as (select * from invoice_nomenclature_rn where rn = 1)
                ,leads_groupped as (select inn, min(dateAdd) as min_lead_date from j28046070_sandbox.view_leads group by inn)
                ,receipts_filtered as (
                	select rd.invoice_id, sum(rd.receipt_amount) as receipt_amount, max(r.receipt_dt) as receipt_dt
                	from j28046070_sandbox.receipts_1c as r
                	join j28046070_sandbox.receipts_detailed_1c as rd on r.receipt_id=rd.receipt_id
                	where r.is_posted and not r.is_deleted
                	group by rd.invoice_id
                	)
                ,report_invoices as (
                	select i.invoice_id, i.invoice_number, i.invoice_dt
                		,DATE_ADD(cast(i.invoice_dt as date), INTERVAL (6 - WEEKDAY(cast(i.invoice_dt as date))) DAY) as invoice_week
                		,case when p.partner_inn = '2310229806' and p.partner_name = 'МЕДИЦИНА ООО' then 'Пермь' 
                			  when p.partner_inn = '2310229806' and p.partner_name = 'ООО МЕДИЦИНА Краснодар' then 'Краснодар'
                			  when p.partner_inn = '3900034752' and p.partner_name = 'СТОМАТОЛОГИЯ ТОМСК' then 'Томск'
                			  when p.partner_inn = '3900034752' and p.partner_name = 'СТОМАТОЛОГИЯ КАЛИНИНГРАД ООО' then 'Калининград'
                			  when p.partner_inn = '4205421649' and p.partner_name = 'ООО КОМАНДА МЕЧТЫ КЕМЕРОВО' then 'Кемерово'
                			  when p.partner_inn = '4205421649' and p.partner_name = 'ООО КОМАНДА МЕЧТЫ КЕМЕРОВО Новокузнецк' then 'Новокузнецк'
                			  else '' 
                		end as city_invoice
                		,n.nomenclature_text, coalesce(n.nomenclature_text_gr, 'Прочее') as nomenclature_text_gr
                		,case when not i.is_posted then 'Не опубликован'
                			  when i.is_deleted then 'Удален'
                			  else 'Корректный'
                		end as invoice_status
                		,o.organization_name, o.organization_inn
                		,p.partner_name, p.partner_inn, p.partner_type
                		,i.invoice_amount
                		,coalesce(r.receipt_amount, 0) as receipt_amount, r.receipt_dt
                		,case when coalesce(r.receipt_amount, 0) = 0 then 'Не оплачен'
                			  when r.receipt_amount > 0 and r.receipt_amount < i.invoice_amount then 'Оплачен частично'
                			  when r.receipt_amount = i.invoice_amount then 'Оплачен'
                			  when r.receipt_amount > i.invoice_amount then 'Оплата больше счета'
                			  else '!!!ERROR!!!'
                		end as invoice_payment_status
                		,case when lg.inn is null then 'Нет лидов'
                			  when i.invoice_dt < lg.min_lead_date then 'До первого лида'
                			  else 'Корректный'
                		end as invoice_details
                	from j28046070_sandbox.invoice_1c as i
                	left join invoice_nomenclature as n on i.invoice_id=n.invoice_id
                	left join receipts_filtered as r on i.invoice_id=r.invoice_id
                	left join j28046070_sandbox.organizations_1c as o on i.organization_id=o.organization_id -- and not o.is_deleted
                	left join j28046070_sandbox.partners_1c as p on i.partner_id=p.partner_id -- and not p.is_deleted
                	left join leads_groupped as lg on p.partner_inn = lg.inn
                	)
                select * from report_invoices"""

    mysql_update_view(
        db_user=DB_SUPER_USER,
        db_password=DB_SUPER_PASSWORD,
        db_host=DB_HOST,
        db_port=DB_PORT,
        db_dbname='j28046070_leads',
        tbl_name=TBL_NAME,
        tbl_db=TBL_DB,
        query=QUERY,
        big_query_flag=True
    )


    ########################################################################################################################
    TBL_DB = 'j28046070_sandbox'
    TBL_NAME = 'view_payment_method'
    QUERY = f"""insert into {TBL_DB}.{TBL_NAME}
                with 
                 partners_1c_rn as (select partner_inn, partner_name, row_number() over(partition by partner_inn order by partner_number desc) as rn from j28046070_sandbox.partners_1c)
                ,partners_1c_final as (select partner_inn, partner_name from partners_1c_rn where rn = 1)
                ,legalEntity_rn as (select inn, legalEntity, row_number() over(partition by inn order by dateTimeAdd desc) as rn from j28046070_sandbox.view_leads)
                ,legalEntity_final as (select inn, legalEntity from legalEntity_rn where rn = 1)
                ,payment_method_rn as (
                	select *, row_number() over(partition by inn order by payment_type) as rn 
                	from j28046070_sandbox.payment_method)
                ,payment_method_final as (select * from payment_method_rn where rn = 1)
                ,view_leads_groupped as (select distinct inn from j28046070_sandbox.view_leads)
                ,final as (
                	select project, legal_entity, inn, deposit_min_value, deposit_average_value, payment_type, comment, flg_stop from payment_method_final
                	UNION
                	select 'нет инфо' as project
                		,coalesce(pf.partner_name, lef.legalEntity, 'нет инфо') as legal_entity
                		,vlg.inn as inn
                		,0 as deposit_min_value
                		,0 as deposit_average_value
                		,'постоплата. еженедельно' as payment_type
                		,'Заполнить Google таблицу' as comment
                		,'' as flg_stop
                	from view_leads_groupped as vlg 
                	left join payment_method_final as pmf on vlg.inn = pmf.inn
                	left join partners_1c_final as pf on vlg.inn = pf.partner_inn
                	left join legalEntity_final as lef on vlg.inn = lef.inn
                	where pmf.inn is null
                	)
                select * from final"""

    mysql_update_view(
        db_user=DB_SUPER_USER,
        db_password=DB_SUPER_PASSWORD,
        db_host=DB_HOST,
        db_port=DB_PORT,
        db_dbname='j28046070_leads',
        tbl_name=TBL_NAME,
        tbl_db=TBL_DB,
        query=QUERY,
        big_query_flag=True
    )


    ########################################################################################################################
    TBL_DB = 'j28046070_sandbox'
    TBL_NAME = 'view_invoice_report'
    QUERY = rf"""insert into {TBL_DB}.{TBL_NAME}
                with 
                 partners_1c_city as (
                	select partner_inn, partner_name
                		,case when partner_inn = '2310229806' and partner_name = 'ООО МЕДИЦИНА Краснодар' then 'Краснодар'
                			  when partner_inn = '3900034752' and partner_name = 'СТОМАТОЛОГИЯ ТОМСК' then 'Томск'
                			  when partner_inn = '3900034752' and partner_name = 'СТОМАТОЛОГИЯ КАЛИНИНГРАД ООО' then 'Калининград'
                			  when partner_inn = '4205421649' and partner_name = 'ООО КОМАНДА МЕЧТЫ КЕМЕРОВО' then 'Кемерово'
                			  when partner_inn = '4205421649' and partner_name = 'ООО КОМАНДА МЕЧТЫ КЕМЕРОВО Новокузнецк' then 'Новокузнецк' 
                			  else ''
                		end as city_invoice
                	from j28046070_sandbox.partners_1c)
                ,partners_1c_rn as (
                	select partner_inn, city_invoice, partner_name
                		,row_number() over(partition by partner_inn, city_invoice order by partner_name) as rn 
                	from partners_1c_city
                	)
                ,partners_1c_final as (select partner_inn, city_invoice, partner_name from partners_1c_rn where rn = 1)
                ,payment_method_intervals as (
                	select *
                		,case when payment_type = 'депозит' then cast('2000-01-01' as date)
                			  when payment_type = 'постоплата. еженедельно' then DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) + 7 DAY)
                			  when payment_type = 'постоплата. 15 и 30' and DAY(CURDATE()) <= 15 then DATE_FORMAT(DATE_SUB(CURDATE(), INTERVAL DAY(CURDATE()) DAY), '%%Y-%%m-16')
                			  when payment_type = 'постоплата. 15 и 30' and DAY(CURDATE()) >  15 then DATE_FORMAT(CURDATE(), '%%Y-%%m-01')
                			  when payment_type = 'постоплата. ежемесячно' then DATE_FORMAT(DATE_SUB(CURDATE(), INTERVAL DAY(CURDATE()) DAY), '%%Y-%%m-01')
                		end as leads_start
                		,case when payment_type = 'депозит' then DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) + 1 DAY)
                			  when payment_type = 'постоплата. еженедельно' then DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) + 1 DAY)
                			  when payment_type = 'постоплата. 15 и 30' and DAY(CURDATE()) <= 15 then DATE_SUB(CURDATE(), INTERVAL DAY(CURDATE()) DAY)
                			  when payment_type = 'постоплата. 15 и 30' and DAY(CURDATE()) >  15 then DATE_FORMAT(CURDATE(), '%%Y-%%m-15')
                			  when payment_type = 'постоплата. ежемесячно' then DATE_SUB(CURDATE(), INTERVAL DAY(CURDATE()) DAY)
                		end as leads_end
                		,case when payment_type = 'постоплата. 15 и 30' and DAY(CURDATE()) <= 15 then DATE_FORMAT(DATE_SUB(CURDATE(), INTERVAL DAY(CURDATE()) DAY), '%%Y-%%m-16')
                			  when payment_type = 'постоплата. 15 и 30' and DAY(CURDATE()) >  15 then DATE_FORMAT(CURDATE(), '%%Y-%%m-01')
                			  when payment_type = 'постоплата. ежемесячно' then DATE_FORMAT(DATE_SUB(CURDATE(), INTERVAL DAY(CURDATE()) DAY), '%%Y-%%m-01')
                			  else DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) + 7 DAY) 
                		end as leads_prev_start
                		,case when payment_type = 'постоплата. 15 и 30' and DAY(CURDATE()) <= 15 then DATE_SUB(CURDATE(), INTERVAL DAY(CURDATE()) DAY)
                			  when payment_type = 'постоплата. 15 и 30' and DAY(CURDATE()) >  15 then DATE_FORMAT(CURDATE(), '%%Y-%%m-15')
                			  when payment_type = 'постоплата. ежемесячно' then DATE_SUB(CURDATE(), INTERVAL DAY(CURDATE()) DAY)
                			  else DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) + 1 DAY)
                		end as leads_prev_end
                		,case when payment_type = 'депозит' then cast('2000-01-01' as date)
                			  when payment_type = 'постоплата. еженедельно' then DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) DAY)
                			  when payment_type = 'постоплата. 15 и 30' and DAY(CURDATE()) <= 15 then DATE_FORMAT(CURDATE(), '%%Y-%%m-01')
                			  when payment_type = 'постоплата. 15 и 30' and DAY(CURDATE()) >  15 then DATE_FORMAT(CURDATE(), '%%Y-%%m-16')
                			  when payment_type = 'постоплата. ежемесячно' then DATE_FORMAT(CURDATE(), '%%Y-%%m-01')
                		end as invoice_start
                		,case when payment_type = 'депозит' then DATE_ADD(CURDATE(), INTERVAL (6 - WEEKDAY(CURDATE())) DAY)
                			  when payment_type = 'постоплата. еженедельно' then DATE_ADD(CURDATE(), INTERVAL (6 - WEEKDAY(CURDATE())) DAY)
                			  when payment_type = 'постоплата. 15 и 30' and DAY(CURDATE()) <= 15 then DATE_FORMAT(CURDATE(), '%%Y-%%m-15')
                			  when payment_type = 'постоплата. 15 и 30' and DAY(CURDATE()) >  15 then LAST_DAY(CURDATE())
                			  when payment_type = 'постоплата. ежемесячно' then LAST_DAY(CURDATE())
                		end as invoice_end
                		,case when payment_type = 'постоплата. 15 и 30' and DAY(CURDATE()) <= 15 then DATE_FORMAT(CURDATE(), '%%Y-%%m-01')
                			  when payment_type = 'постоплата. 15 и 30' and DAY(CURDATE()) >  15 then DATE_FORMAT(CURDATE(), '%%Y-%%m-16')
                			  when payment_type = 'постоплата. ежемесячно' then DATE_FORMAT(CURDATE(), '%%Y-%%m-01')
                			  else DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) DAY)
                		end as invoice_curr_start
                		,case when payment_type = 'постоплата. 15 и 30' and DAY(CURDATE()) <= 15 then DATE_FORMAT(CURDATE(), '%%Y-%%m-15')
                			  when payment_type = 'постоплата. 15 и 30' and DAY(CURDATE()) >  15 then LAST_DAY(CURDATE())
                			  when payment_type = 'постоплата. ежемесячно' then LAST_DAY(CURDATE())
                			  else DATE_ADD(CURDATE(), INTERVAL (6 - WEEKDAY(CURDATE())) DAY)
                		end as invoice_curr_end
                	from j28046070_sandbox.view_payment_method)
                ,leads_groupped as (
                	select vl.inn, vl.city_invoice
                		,count(*) as total_cnt
                		,max(vl.dateTimeAdd) as last_lead_dttm
                		,sum(vl.purchase) as total_purchase
                		,sum(vl.sale) as total_sale
                		,sum(case when vl.dateAdd between pmi.leads_start and pmi.leads_end then 1 else 0 end) as interval_cnt
                		,sum(case when vl.dateAdd between pmi.leads_start and pmi.leads_end then vl.purchase else 0 end) as interval_purchase
                		,sum(case when vl.dateAdd between pmi.leads_start and pmi.leads_end then vl.sale else 0 end) as interval_sale
                		,sum(case when vl.dateAdd between pmi.leads_prev_start and pmi.leads_prev_end then 1 else 0 end) as prev_cnt
                		,sum(case when vl.dateAdd between pmi.leads_prev_start and pmi.leads_prev_end then vl.purchase else 0 end) as prev_purchase
                		,sum(case when vl.dateAdd between pmi.leads_prev_start and pmi.leads_prev_end then vl.sale else 0 end) as prev_sale
                	from j28046070_sandbox.view_leads as vl 
                	join payment_method_intervals as pmi on vl.inn = pmi.inn
                	where vl.duplicateFlag = ''
                	group by vl.inn, vl.city_invoice)
                ,invoices_groupped as (
                	select vi.partner_inn as inn, vi.city_invoice
                		,sum(invoice_amount) as total_invoice
                		,sum(receipt_amount) as total_receipt
                		,sum(case when vi.invoice_dt between pmi.invoice_start and pmi.invoice_end then vi.invoice_amount else 0 end) as interval_invoice
                		,sum(case when vi.invoice_dt between pmi.invoice_start and pmi.invoice_end then vi.receipt_amount else 0 end) as interval_receipt
                		,sum(case when vi.invoice_dt between pmi.invoice_curr_start and pmi.invoice_curr_end then vi.invoice_amount else 0 end) as curr_invoice
                		,sum(case when vi.invoice_dt between pmi.invoice_curr_start and pmi.invoice_curr_end then vi.receipt_amount else 0 end) as curr_receipt
                	from j28046070_sandbox.view_invoices as vi
                	join payment_method_intervals as pmi on vi.partner_inn = pmi.inn
                	where 1=1
                	and vi.invoice_status = 'Корректный' 
                	and vi.invoice_details in ('Корректный', 'До первого лида', 'Нет лидов')
                	and vi.nomenclature_text_gr = 'Лиды'
                	group by vi.partner_inn, vi.city_invoice
                	)
                ,invoices_corrected as (
                	select inn, city_invoice, total_invoice, total_receipt, interval_invoice, interval_receipt
                		,case when interval_receipt > interval_invoice then interval_receipt else interval_invoice end as interval_invoice_corrected
                		,curr_invoice, curr_receipt
                	from invoices_groupped
                	)
                ,report as (
                	select l.inn, pmi.project, coalesce(pf.partner_name, pmi.legal_entity) as legal_entity, l.city_invoice
                		,'Данные по способу оплаты' as txt_payment_type
                		,pmi.payment_type
                		,pmi.deposit_min_value
                		,pmi.deposit_average_value
                		,'Данные за отчетный период' as txt_interval_leads
                		,concat('лиды за период c ', date_format(leads_start, '%%Y-%%m-%%d'), ' по ', date_format(leads_end, '%%Y-%%m-%%d')) AS interval_leads
                		,l.interval_cnt
                		,l.interval_purchase
                		,l.interval_sale
                		,concat('счета за период c ', date_format(invoice_start, '%%Y-%%m-%%d'), ' по ', date_format(invoice_end, '%%Y-%%m-%%d')) AS interval_invoices
                		,coalesce(i.interval_invoice, 0) as interval_invoice
                		,coalesce(i.interval_receipt, 0) as interval_receipt
                		,coalesce(corr.correction, 0) as interval_correction
                		,'(счета - лиды) за период' as txt_interval_invoice
                		,coalesce(i.interval_invoice, 0) + coalesce(corr.correction, 0) - l.interval_sale as interval_leads_minus_invoices
                		,case when l.prev_cnt = 0 
                				or i.curr_invoice > 0 
                				or coalesce(i.interval_invoice, 0) + coalesce(corr.correction, 0) - l.interval_sale >= pmi.deposit_min_value
                			  then 'Нет'
                			  else 'Да'
                		end as new_invoice_flag
                		,case when l.prev_cnt = 0 then concat('Нет лидов с ', date_format(leads_prev_start, '%%Y-%%m-%%d'), 'по ', date_format(leads_prev_end, '%%Y-%%m-%%d'))
                			  when i.curr_invoice > 0 then concat('Уже выставлен счет с ', date_format(invoice_curr_start, '%%Y-%%m-%%d'), ' по ', date_format(invoice_curr_end, '%%Y-%%m-%%d'))
                			  when pmi.payment_type = 'депозит' and coalesce(i.interval_invoice_corrected, 0) + coalesce(corr.correction, 0) - l.interval_sale >= pmi.deposit_min_value then 'Остаток больше депозита'
                			  when coalesce(i.interval_invoice_corrected, 0) + coalesce(corr.correction, 0) - l.interval_sale >= 0 then 'Сумма выставленных счетов >= Стоимости лидов'
                			  else ''
                		end as new_invoice_description
                		,case when coalesce(i.interval_invoice_corrected, 0) + coalesce(corr.correction, 0) - l.interval_sale < pmi.deposit_min_value and l.prev_cnt > 0 and i.curr_invoice = 0
                			then
                				case when pmi.payment_type = 'депозит' and coalesce(i.interval_invoice_corrected, 0) + coalesce(corr.correction, 0) - l.interval_sale >= 0 then pmi.deposit_min_value
                					 when pmi.payment_type = 'депозит' and coalesce(i.interval_invoice_corrected, 0) + coalesce(corr.correction, 0) - l.interval_sale < 0 then pmi.deposit_min_value + (l.interval_sale - coalesce(i.interval_invoice, 0))
                				  	 else pmi.deposit_average_value - coalesce(i.interval_invoice_corrected, 0) + l.interval_sale
                				end
                			else 0 
                		end as new_invoice_amount
                		,'Данные за всю историю' as txt_total_leads
                		,l.total_cnt
                		,l.total_purchase
                		,l.total_sale
                		,'Данные за всю историю' as txt_total_invoices
                		,coalesce(i.total_invoice, 0) + coalesce(corr.correction, 0) as total_invoice
                		,coalesce(i.total_receipt, 0) + coalesce(corr.correction, 0) as receipt_total
                		,'(счета - лиды) за всю историю' as txt5
                		,coalesce(i.total_invoice, 0) + coalesce(corr.correction, 0) - l.total_sale as invoice_total_check
                		,case when coalesce(i.total_invoice, 0) + coalesce(corr.correction, 0) - l.total_sale < pmi.deposit_min_value
                			  then pmi.deposit_average_value - coalesce(i.total_invoice, 0) - coalesce(corr.correction, 0) + l.total_sale
                			  else 0 end as total_check
                		,'проверка необходимости выставления счетов' txt_check
                		,l.prev_cnt
                		,l.prev_purchase
                		,l.prev_sale
                		,coalesce(i.curr_invoice, 0) as curr_invoice
                		,coalesce(i.curr_receipt, 0) as curr_receipt
                		,l.last_lead_dttm as last_lead_dttm
                		,'техническая информация' as txt_comment
                		,pmi.comment
                	from leads_groupped as l
                	left join invoices_corrected as i on l.inn = i.inn and l.city_invoice = i.city_invoice
                	left join payment_method_intervals as pmi on l.inn = pmi.inn
                	left join j28046070_sandbox.deposit_corrections as corr on l.inn = corr.inn
                	left join partners_1c_final as pf on l.inn = pf.partner_inn and l.city_invoice = pf.city_invoice
                	)
                select * from report"""

    mysql_update_view(
        db_user=DB_SUPER_USER,
        db_password=DB_SUPER_PASSWORD,
        db_host=DB_HOST,
        db_port=DB_PORT,
        db_dbname='j28046070_leads',
        tbl_name=TBL_NAME,
        tbl_db=TBL_DB,
        query=QUERY,
        big_query_flag=True
    )


    ########################################################################################################################
    TBL_DB = 'j28046070_sandbox'
    TBL_NAME = 'view_new_invoices'
    QUERY = rf"""insert into {TBL_DB}.{TBL_NAME}
                select inn, project, legal_entity
                	,payment_type, deposit_min_value, deposit_average_value
                	,interval_sale, interval_invoice, interval_invoice - interval_sale as invoice_minus_sale
                	,new_invoice_flag, new_invoice_description, new_invoice_amount
                from j28046070_sandbox.view_invoice_report
                where interval_correction + interval_invoice - interval_sale < deposit_min_value
                order by new_invoice_flag, interval_invoice - interval_sale"""

    mysql_update_view(
        db_user=DB_SUPER_USER,
        db_password=DB_SUPER_PASSWORD,
        db_host=DB_HOST,
        db_port=DB_PORT,
        db_dbname='j28046070_leads',
        tbl_name=TBL_NAME,
        tbl_db=TBL_DB,
        query=QUERY,
        big_query_flag=True
    )