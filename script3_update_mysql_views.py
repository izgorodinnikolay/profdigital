import os
from dotenv import load_dotenv
from func_update_data_on_mysql import mysql_update_view_with_retry

def run_script_update_mysql_views():

    load_dotenv('variables.env')

    ########################################################################################################################
    # VARIABLES

    # MySQL
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = int(os.getenv("DB_PORT"))
    DB_DBNAME = os.getenv("DB_DBNAME")
    DB_SUPER_USER = os.getenv("DB_SUPER_USER")
    DB_SUPER_PASSWORD = os.getenv("DB_SUPER_PASSWORD")
    DB_SUPER_DBNAME = os.getenv("DB_SUPER_DBNAME")
    MAX_RETRIES = int(os.getenv("MAX_RETRIES"))
    RETRY_SLEEP_SECONDS = int(os.getenv("RETRY_SLEEP_SECONDS"))

    print(f'starting run_script_update_mysql_views')

    ########################################################################################################################
    TBL_DB = 'j28046070_sandbox'
    TBL_NAME = 'view_leads'
    ANALYZE_TABLES = ['j28046070_leads.leads']
    QUERY = f"""insert into {TBL_DB}.{TBL_NAME}
    select l.project, l.dateAdd, l.dateTimeAdd
    	,DATE_ADD(l.dateAdd, INTERVAL (6 - WEEKDAY(l.dateAdd)) DAY) as week_end
    	,case when l.inn = '720307197077' then '2463115644'
              when l.inn = '761107378757' then '760212666248'
    	      when length(l.inn) in (9, 11) then concat('0', l.inn) else l.inn end as inn
    	,case when l.inn in ('2310229806', '3900034752', '4205421649', '7727471830') then l.city else '' end as city_invoice
    	,case when l.inn in ('9701285618','7733331140','5047309883','9713010350','9703181910') then 
    			case when l.source like 'АЛЭ%%' then 'АЛЭ'
    				 when l.source like 'ЛЭ%%' then 'ЛЭ'
    				 when l.source like 'РМ%%' then 'РМ'
    				 else '' end
    		  else '' end as source_invoice
    	,l.legalEntity, l.source, l.company, l.name, l.phone, l.city
    	,l.branch, l.sendStatus, l.sendDateTime, l.purchase, l.sale
    	,case when row_number() 
    			   over(partition by l.inn, l.phone, l.source, 
    	                             case when l.inn in ('2310229806', '3900034752', '4205421649', '7727471830') then l.city else '' end,
    	                             l.dateAdd - INTERVAL (DAY(l.dateAdd) - 1) DAY 
    	                order by l.dateTimeAdd
    	               ) > 1 then 'Дубликат' else '' end as duplicateFlag
    from j28046070_leads.leads as l"""

    mysql_update_view_with_retry(
        db_user=DB_SUPER_USER,
        db_password=DB_SUPER_PASSWORD,
        db_host=DB_HOST,
        db_port=DB_PORT,
        db_dbname='j28046070_leads',
        tbl_name=TBL_NAME,
        tbl_db=TBL_DB,
        query=QUERY,
        big_query_flag=True,
        analyze_tables=ANALYZE_TABLES,
        max_retries=MAX_RETRIES,
        retry_sleep_seconds=RETRY_SLEEP_SECONDS
    )


    ########################################################################################################################
    TBL_DB = 'j28046070_sandbox'
    TBL_NAME = 'view_payment_method'
    ANALYZE_TABLES = ['j28046070_sandbox.view_leads', 'j28046070_sandbox.payment_method']
    QUERY = f"""insert into {TBL_DB}.{TBL_NAME}
    with
    inn_from_leads as (
        select inn, legalEntity
        from (
            select inn, legalEntity, ROW_NUMBER() OVER (PARTITION BY inn ORDER BY dateTimeAdd DESC) AS rn
            from j28046070_sandbox.view_leads
        ) t
        where rn = 1
    ),
    inn_from_google as (
        select *
        from (
            select *, ROW_NUMBER() OVER (PARTITION BY inn ORDER BY payment_type) AS rn
            from j28046070_sandbox.payment_method
        ) t
        where rn = 1
    ),
    inn_all as (
    	select project, legal_entity, inn, deposit_min_value, deposit_average_value, payment_type, comment, flg_stop
    	from inn_from_google
    	union all
    	select
    	    'нет инфо' as project,
    	    legalEntity as legal_entity,
    	    inn AS inn,
    	    0 AS deposit_min_value,
    	    0 AS deposit_average_value,
    	    'постоплата. еженедельно' as payment_type,
    	    'Заполнить Google таблицу' as comment,
    	    '' as flg_stop
    	from inn_from_leads ifl
    	where not exists (select 1 from j28046070_sandbox.payment_method pm where pm.inn = ifl.inn)
    ),
    dt as (
    	select cast('2000-01-01' AS DATE) AS day_20000101
    		,DATE_SUB(CURDATE(), INTERVAL 1 DAY) yesterday
    		,DATE_FORMAT(DATE_SUB(CURDATE(), INTERVAL DAY(CURDATE()) DAY), '%%Y-%%m-01') prev_month_01
    		,DATE_FORMAT(DATE_SUB(CURDATE(), INTERVAL DAY(CURDATE()) DAY), '%%Y-%%m-16') prev_month_16
    		,DATE_SUB(CURDATE(), INTERVAL DAY(CURDATE()) DAY) prev_month_end
    		,DATE_FORMAT(CURDATE(), '%%Y-%%m-01') curr_month_01
    		,DATE_FORMAT(CURDATE(), '%%Y-%%m-15') curr_month_15
    		,DATE_FORMAT(CURDATE(), '%%Y-%%m-16') curr_month_16
    		,LAST_DAY(CURDATE()) curr_month_end
    		,DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) + 7 DAY) prev_week_start
    		,DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) + 1 DAY) prev_week_end
    		,DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) DAY) curr_week_start
    		,DATE_ADD(CURDATE(), INTERVAL (6 - WEEKDAY(CURDATE())) DAY) curr_week_end
    )
    select i.project, i.legal_entity, i.inn, i.deposit_min_value, i.deposit_average_value
    	,i.payment_type, i.comment, i.flg_stop
    	,case when i.payment_type = 'депозит' then dt.day_20000101
              when i.payment_type = 'постоплата. 15 и 30' and DAY(CURDATE()) <= 15 then dt.prev_month_16
              when i.payment_type = 'постоплата. 15 и 30' and DAY(CURDATE()) > 15 then dt.curr_month_01
              when i.payment_type = 'постоплата. ежемесячно' then dt.prev_month_01
              else dt.prev_week_start end as leads_start
    	,case when i.payment_type = 'депозит' then dt.yesterday
              when i.payment_type = 'постоплата. 15 и 30' and DAY(CURDATE()) <= 15 then dt.prev_month_end
              when i.payment_type = 'постоплата. 15 и 30' and DAY(CURDATE()) > 15 then dt.curr_month_15
              when i.payment_type = 'постоплата. ежемесячно' then dt.prev_month_end
              else dt.prev_week_end end as leads_end
    	,case when i.payment_type = 'постоплата. 15 и 30' and DAY(CURDATE()) <= 15 then prev_month_16
              when i.payment_type = 'постоплата. 15 и 30' and DAY(CURDATE()) > 15 then curr_month_01
              when i.payment_type = 'постоплата. ежемесячно' then prev_month_01
              else dt.prev_week_start end as leads_prev_start
    	,case when i.payment_type = 'депозит' then dt.yesterday
    		  when i.payment_type = 'постоплата. 15 и 30' and DAY(CURDATE()) <= 15 then prev_month_end
              when i.payment_type = 'постоплата. 15 и 30' and DAY(CURDATE()) > 15 then curr_month_15
              when i.payment_type = 'постоплата. ежемесячно' then prev_month_end
              else prev_week_end end as leads_prev_end
    	,case when i.payment_type = 'депозит' then dt.day_20000101
              when i.payment_type = 'постоплата. 15 и 30' and DAY(CURDATE()) <= 15 then dt.curr_month_01
              when i.payment_type = 'постоплата. 15 и 30' and DAY(CURDATE()) > 15 then dt.curr_month_16
              when i.payment_type = 'постоплата. ежемесячно' then dt.curr_month_01
              else dt.curr_week_start end as invoice_start
    	,case when i.payment_type IN ('депозит', 'постоплата. еженедельно') then dt.curr_week_end
              when i.payment_type = 'постоплата. 15 и 30' and DAY(CURDATE()) <= 15 then dt.curr_month_15
              when i.payment_type = 'постоплата. 15 и 30' and DAY(CURDATE()) > 15 then dt.curr_month_end
              when i.payment_type = 'постоплата. ежемесячно' then dt.curr_month_end
              else dt.curr_week_end end as invoice_end
    	,case when i.payment_type = 'постоплата. 15 и 30' and DAY(CURDATE()) <= 15 then dt.curr_month_01
              when i.payment_type = 'постоплата. 15 и 30' and DAY(CURDATE()) > 15 then dt.curr_month_16
              when i.payment_type = 'постоплата. ежемесячно' then dt.curr_month_01
              else dt.curr_week_start end as invoice_curr_start
    	,case when i.payment_type = 'постоплата. 15 и 30' AND DAY(CURDATE()) <= 15 then dt.curr_month_15
              when i.payment_type = 'постоплата. 15 и 30' AND DAY(CURDATE()) > 15 then dt.curr_month_end
              when i.payment_type = 'постоплата. ежемесячно' then dt.curr_month_end
              else dt.curr_week_end end as invoice_curr_end
    from inn_all i cross join dt"""

    mysql_update_view_with_retry(
        db_user=DB_SUPER_USER,
        db_password=DB_SUPER_PASSWORD,
        db_host=DB_HOST,
        db_port=DB_PORT,
        db_dbname='j28046070_leads',
        tbl_name=TBL_NAME,
        tbl_db=TBL_DB,
        query=QUERY,
        big_query_flag=True,
        analyze_tables=ANALYZE_TABLES,
        max_retries=MAX_RETRIES,
        retry_sleep_seconds=RETRY_SLEEP_SECONDS
    )


    ########################################################################################################################
    TBL_DB = 'j28046070_sandbox'
    TBL_NAME = 'view_invoices'
    ANALYZE_TABLES = ['j28046070_sandbox.invoice_1c',
                      'j28046070_sandbox.invoice_detailed_1c',
                      'j28046070_sandbox.receipts_1c',
                      'j28046070_sandbox.receipts_detailed_1c',
                      'j28046070_sandbox.organizations_1c',
                      'j28046070_sandbox.partners_1c']
    QUERY = f"""insert into {TBL_DB}.{TBL_NAME}
    with 
    invoice_nomenclature as (
        select invoice_id, nomenclature_text_gr, nomenclature_text
        from (
            select invoice_id, nomenclature_text_gr, nomenclature_text,
                   row_number() over(partition by invoice_id order by amount desc) as rn 
            from j28046070_sandbox.invoice_detailed_1c
        ) t
        where rn = 1
    ),
    receipts_gr as (
        select rd.invoice_id, SUM(rd.receipt_amount) AS receipt_amount, MAX(r.receipt_dt) AS receipt_dt
        from j28046070_sandbox.receipts_1c AS r
        join j28046070_sandbox.receipts_detailed_1c AS rd ON r.receipt_id = rd.receipt_id
        where r.is_posted = 1 AND r.is_deleted = 0
        group by  rd.invoice_id
    )
    select i.invoice_id, i.invoice_number, i.invoice_dt
    	,case when p.partner_inn = '2310229806' and p.partner_name = 'МЕДИЦИНА ООО' then 'Пермь' 
              when p.partner_inn = '2310229806' and p.partner_name = 'ООО МЕДИЦИНА Краснодар' then 'Краснодар'
              when p.partner_inn = '2310229806' and p.partner_name = 'ООО «МЕДИЦИНА» Обособленное подразделение Саратов' then 'Саратов'
              when p.partner_inn = '3900034752' and p.partner_name = 'СТОМАТОЛОГИЯ ТОМСК' then 'Томск'
              when p.partner_inn = '3900034752' and p.partner_name = 'СТОМАТОЛОГИЯ КАЛИНИНГРАД ООО' then 'Калининград'
              when p.partner_inn = '4205421649' and p.partner_name = 'ООО КОМАНДА МЕЧТЫ КЕМЕРОВО' then 'Кемерово'
              when p.partner_inn = '4205421649' and p.partner_name = 'ООО КОМАНДА МЕЧТЫ КЕМЕРОВО Новокузнецк' then 'Новокузнецк'
              when p.partner_inn = '7727471830' and p.partner_name = 'ЕВРОМЕД Екб ООО' then 'Екатеринбург'
              when p.partner_inn = '7727471830' and p.partner_name = 'ЕВРОМЕД ООО' then 'Москва'
              else '' end as city_invoice
    	,case when p.partner_inn in ('9701285618','7733331140','5047309883','9713010350','9703181910') then 
    		case when i.invoice_comment = 'Александрит' then 'АЛЭ'
              	 when i.invoice_comment = 'массаж' then 'РМ' 
                 else 'ЛЭ' end 
              else '' end as source_invoice
        ,n.nomenclature_text, coalesce(n.nomenclature_text_gr, 'Прочее') as nomenclature_text_gr
        ,case when i.is_posted = 0 then 'Не опубликован' 
              when i.is_deleted = 1 then 'Удален'
              else 'Корректный' end as invoice_status
        ,o.organization_name
        ,o.organization_inn
        ,p.partner_name
        ,p.partner_inn
        ,p.partner_type
        ,i.invoice_amount
        ,coalesce(r.receipt_amount, 0) AS receipt_amount
        ,r.receipt_dt
        ,case when coalesce(r.receipt_amount, 0) = 0 then 'Не оплачен'
              when r.receipt_amount > 0 AND r.receipt_amount < i.invoice_amount then 'Оплачен частично'
              when r.receipt_amount = i.invoice_amount then 'Оплачен'
              when r.receipt_amount > i.invoice_amount then 'Оплата больше счета'
              else '!!!ERROR!!!' end as invoice_payment_status
        ,case when i.partner_id = 'af3fca58-381d-11f1-8bfb-00155d46fc0e' then '489879c0-8cc9-11f1-9b62-00155d46fc0e' else i.partner_id
        end as partner_id
    from j28046070_sandbox.invoice_1c i
    left join invoice_nomenclature n on i.invoice_id = n.invoice_id
    left join receipts_gr r on i.invoice_id = r.invoice_id
    left join j28046070_sandbox.organizations_1c o on i.organization_id = o.organization_id
    left join j28046070_sandbox.partners_1c p on 
        case when i.partner_id = 'af3fca58-381d-11f1-8bfb-00155d46fc0e' then '489879c0-8cc9-11f1-9b62-00155d46fc0e' else i.partner_id
        end = p.partner_id"""

    mysql_update_view_with_retry(
        db_user=DB_SUPER_USER,
        db_password=DB_SUPER_PASSWORD,
        db_host=DB_HOST,
        db_port=DB_PORT,
        db_dbname='j28046070_leads',
        tbl_name=TBL_NAME,
        tbl_db=TBL_DB,
        query=QUERY,
        big_query_flag=True,
        analyze_tables=ANALYZE_TABLES,
        max_retries=MAX_RETRIES,
        retry_sleep_seconds=RETRY_SLEEP_SECONDS
    )


    ########################################################################################################################
    TBL_DB = 'j28046070_sandbox'
    TBL_NAME = 'view_invoice_report'
    ANALYZE_TABLES = ['j28046070_sandbox.view_leads',
                      'j28046070_sandbox.view_invoices',
                      'j28046070_sandbox.view_payment_method',
                      'j28046070_sandbox.partners_1c',
                      'j28046070_sandbox.contract_1c',
                      'j28046070_sandbox.organizations_1c',
                      'j28046070_sandbox.individuals_1c']
    QUERY = rf"""insert into {TBL_DB}.{TBL_NAME}
    with 
    leads_groupped as (
    	select vl.inn, vl.city_invoice, vl.source_invoice
    		,sum(case when vl.sale > 0 then 1 else 0 end) as total_cnt
    		,max(vl.dateTimeAdd) as last_lead_dttm
    		,sum(vl.purchase) as total_purchase
    		,sum(vl.sale) as total_sale
    		,sum(case when vl.sale > 0 and vl.dateAdd between pmi.leads_start and pmi.leads_end then 1 else 0 end) as interval_cnt
    		,sum(case when vl.dateAdd between pmi.leads_start and pmi.leads_end then vl.purchase else 0 end) as interval_purchase
    		,sum(case when vl.dateAdd between pmi.leads_start and pmi.leads_end then vl.sale else 0 end) as interval_sale
    		,sum(case when vl.sale > 0 and vl.dateAdd between pmi.leads_prev_start and pmi.leads_prev_end then 1 else 0 end) as prev_cnt
    		,sum(case when vl.dateAdd between pmi.leads_prev_start and pmi.leads_prev_end then vl.purchase else 0 end) as prev_purchase
    		,sum(case when vl.dateAdd between pmi.leads_prev_start and pmi.leads_prev_end then vl.sale else 0 end) as prev_sale
    	from j28046070_sandbox.view_leads as vl 
    	join j28046070_sandbox.view_payment_method as pmi on vl.inn = pmi.inn
    	where vl.duplicateFlag = ''
    	group by vl.inn, vl.city_invoice, vl.source_invoice
    ),
    invoices_groupped as (
        select vi.partner_inn as inn, vi.city_invoice, vi.source_invoice
        	-- total
        	,sum(case when vi.invoice_status = 'Корректный' then vi.invoice_amount else 0 end) as total_invoice
        	,case when sum(case when vi.invoice_status = 'Корректный' then vi.receipt_amount else 0 end) > 
        			   sum(case when vi.invoice_status = 'Корректный' then vi.invoice_amount else 0 end)
        		  then sum(case when vi.invoice_status = 'Корректный' then vi.receipt_amount else 0 end)
        		  else sum(case when vi.invoice_status = 'Корректный' then vi.invoice_amount else 0 end) end as total_invoice_corrected
        	,sum(case when vi.invoice_status = 'Корректный' then vi.receipt_amount else 0 end) as total_receipt
        	,max(case when vi.invoice_status = 'Корректный' then vi.invoice_dt else null end) as total_max_invoice_dt
        	-- interval
        	,sum(case when vi.invoice_status = 'Корректный' and vi.invoice_dt between pmi.invoice_start and pmi.invoice_end then vi.invoice_amount else 0 end) as interval_invoice
        	,case when sum(case when vi.invoice_status = 'Корректный' and vi.invoice_dt between pmi.invoice_start and pmi.invoice_end then vi.receipt_amount else 0 end) > 
        			   sum(case when vi.invoice_status = 'Корректный' and vi.invoice_dt between pmi.invoice_start and pmi.invoice_end then vi.invoice_amount else 0 end)
        		  then sum(case when vi.invoice_status = 'Корректный' and vi.invoice_dt between pmi.invoice_start and pmi.invoice_end then vi.receipt_amount else 0 end)
        		  else sum(case when vi.invoice_status = 'Корректный' and vi.invoice_dt between pmi.invoice_start and pmi.invoice_end then vi.invoice_amount else 0 end)
        	end as interval_invoice_corrected
        	,sum(case when vi.invoice_status = 'Корректный' and vi.invoice_dt between pmi.invoice_start and pmi.invoice_end then vi.receipt_amount else 0 end) as interval_receipt
        	,max(case when vi.invoice_status = 'Корректный' and vi.invoice_dt between pmi.invoice_start and pmi.invoice_end then vi.invoice_dt else 0 end) as interval_max_invoice_dt
        	-- current period
        	,sum(case when vi.invoice_dt between pmi.invoice_curr_start and pmi.invoice_curr_end then vi.invoice_amount else null end) as curr_invoice
        	,sum(case when vi.invoice_dt between pmi.invoice_curr_start and pmi.invoice_curr_end then vi.receipt_amount else null end) as curr_receipt
        	,max(case when vi.invoice_dt between pmi.invoice_curr_start and pmi.invoice_curr_end then vi.invoice_dt else null end) as curr_max_invoice_dt
        from j28046070_sandbox.view_invoices as vi
        join j28046070_sandbox.view_payment_method as pmi on vi.partner_inn = pmi.inn
        where 1=1
        and vi.nomenclature_text_gr = 'Лиды'
        group by vi.partner_inn, vi.city_invoice, vi.source_invoice
    ),
    partners as (
     	select *
     	from (
    		select p.partner_inn as inn, p.partner_name, p.partner_id
    			,c.contract_id, c.contract_number, c.currency_id, c.organization_id
    			,o.organization_name, o.organization_inn, o.manager_key
    			,i.individual_number, i.description as individual_description
    			,case when p.partner_inn = '2310229806' and p.partner_name = 'МЕДИЦИНА ООО' then 'Пермь' 
    				  when p.partner_inn = '2310229806' and p.partner_name = 'ООО МЕДИЦИНА Краснодар' then 'Краснодар'
    				  when p.partner_inn = '2310229806' and p.partner_name = 'ООО «МЕДИЦИНА» Обособленное подразделение Саратов' then 'Саратов'
    			      when p.partner_inn = '3900034752' and p.partner_name = 'СТОМАТОЛОГИЯ ТОМСК' then 'Томск'
    			  	  when p.partner_inn = '3900034752' and p.partner_name = 'СТОМАТОЛОГИЯ КАЛИНИНГРАД ООО' then 'Калининград'
    			  	  when p.partner_inn = '4205421649' and p.partner_name = 'ООО КОМАНДА МЕЧТЫ КЕМЕРОВО' then 'Кемерово'
    			  	  when p.partner_inn = '4205421649' and p.partner_name = 'ООО КОМАНДА МЕЧТЫ КЕМЕРОВО Новокузнецк' then 'Новокузнецк' 
                      when p.partner_inn = '7727471830' and p.partner_name = 'ЕВРОМЕД Екб ООО' then 'Екатеринбург'
                      when p.partner_inn = '7727471830' and p.partner_name = 'ЕВРОМЕД ООО' then 'Москва'
    			   	  else '' end as city_invoice
    			,row_number() over(
    				partition by partner_inn,
    					case when p.partner_inn = '2310229806' and p.partner_name = 'МЕДИЦИНА ООО' then 'Пермь' 
    						 when p.partner_inn = '2310229806' and p.partner_name = 'ООО МЕДИЦИНА Краснодар' then 'Краснодар'
    						 when p.partner_inn = '2310229806' and p.partner_name = 'ООО «МЕДИЦИНА» Обособленное подразделение Саратов' then 'Саратов'
    					     when p.partner_inn = '3900034752' and p.partner_name = 'СТОМАТОЛОГИЯ ТОМСК' then 'Томск'
    					  	 when p.partner_inn = '3900034752' and p.partner_name = 'СТОМАТОЛОГИЯ КАЛИНИНГРАД ООО' then 'Калининград'
    					  	 when p.partner_inn = '4205421649' and p.partner_name = 'ООО КОМАНДА МЕЧТЫ КЕМЕРОВО' then 'Кемерово'
    					  	 when p.partner_inn = '4205421649' and p.partner_name = 'ООО КОМАНДА МЕЧТЫ КЕМЕРОВО Новокузнецк' then 'Новокузнецк' 
                             when p.partner_inn = '7727471830' and p.partner_name = 'ЕВРОМЕД Екб ООО' then 'Екатеринбург'
                             when p.partner_inn = '7727471830' and p.partner_name = 'ЕВРОМЕД ООО' then 'Москва'
    					   	 else '' end
    				order by partner_name
    				) rn
    		from j28046070_sandbox.partners_1c p
    		join j28046070_sandbox.contract_1c c on p.partner_id = c.partner_id 
    		join j28046070_sandbox.organizations_1c o on c.organization_id = o.organization_id
    		join j28046070_sandbox.individuals_1c i on o.manager_key = i.individual_id
    		where 1=1
    		and c.is_deleted = 0
    		and c.description = 'Ведение платного трафика'
    		and o.organization_inn = '720307197077'
    		) t
    	where rn = 1
    )
    select lg.inn, pmi.project, coalesce(p.partner_name, pmi.legal_entity) as legal_entity, lg.city_invoice, lg.source_invoice
    	,'Способ оплаты' as txt_payment_type
    	,pmi.payment_type
    	,pmi.deposit_min_value
    	,pmi.deposit_average_value
    	,'Данные за отчетный период' as txt_interval_leads
    	,concat('лиды за период c ', date_format(pmi.leads_start, '%%Y-%%m-%%d'), ' по ', date_format(pmi.leads_end, '%%Y-%%m-%%d')) AS interval_leads
    	,lg.interval_cnt
    	,lg.interval_purchase
    	,lg.interval_sale
    	,concat('счета за период c ', date_format(pmi.invoice_start, '%%Y-%%m-%%d'), ' по ', date_format(pmi.invoice_end, '%%Y-%%m-%%d')) AS interval_invoices
    	,coalesce(ig.interval_invoice, 0) as interval_invoice
    	,coalesce(ig.interval_receipt, 0) as interval_receipt
    	,coalesce(corr.correction, 0) as interval_correction
    	,ig.interval_max_invoice_dt
    	,'(счета - лиды) за период' as txt_interval_invoice
    	,coalesce(ig.interval_invoice_corrected, 0) + coalesce(corr.correction, 0) - lg.interval_sale as interval_leads_minus_invoices
    	,case when pmi.payment_type = 'депозит' then coalesce(ig.interval_invoice_corrected, 0) + coalesce(corr.correction, 0) - lg.interval_sale else 0 
    	end as interval_deposit_balance
    	,case when lg.prev_cnt = 0 
    			or ig.curr_invoice > 0 
    			or coalesce(ig.interval_invoice_corrected, 0) + coalesce(corr.correction, 0) - lg.interval_sale >= pmi.deposit_min_value
    			or p.partner_id is null
    			or p.contract_id is null
    		  then 'Нет'
    		  else 'Да'
    	end as new_invoice_flag
    	,case when lg.prev_cnt = 0 
    			then concat('Нет лидов с ', date_format(pmi.leads_prev_start, '%%Y-%%m-%%d'), ' по ', date_format(pmi.leads_prev_end, '%%Y-%%m-%%d'))
    		  when ig.curr_invoice > 0 
    		  	then concat('Уже выставлен счет с ', date_format(pmi.invoice_curr_start, '%%Y-%%m-%%d'), ' по ', date_format(pmi.invoice_curr_end, '%%Y-%%m-%%d'))
    		  when pmi.payment_type = 'депозит' and coalesce(ig.interval_invoice_corrected, 0) + coalesce(corr.correction, 0) - lg.interval_sale <= pmi.deposit_min_value 
    		  	then 'Остаток меньше или равен мин депозиту'
    		  when coalesce(ig.interval_invoice_corrected, 0) + coalesce(corr.correction, 0) - lg.interval_sale >= 0 
    		  	then 'Сумма выставленных счетов >= Стоимости лидов'
    		  when p.partner_id is null 
    		  	then concat('По ИНН ', lg.inn, ' отсутствуют данные в Catalog_Контрагенты')
    		  when p.contract_id is null 
    		  	then concat('По ИНН ', lg.inn, ' отсутствуют данные в Catalog_ДоговорыКонтрагентов')
    		  	else ''
    	end as new_invoice_description
    	,case when 	lg.prev_cnt = 0 
    			 or ig.curr_invoice > 0 
    			 or pmi.payment_type = 'депозит' and (coalesce(ig.interval_invoice_corrected, 0) + coalesce(corr.correction, 0) - lg.interval_sale) >= pmi.deposit_min_value
    		then 0
    		else
    			case when pmi.payment_type = 'депозит' and coalesce(ig.interval_invoice_corrected, 0) + coalesce(corr.correction, 0) - lg.interval_sale >= 0 
                        then pmi.deposit_average_value
    				 when pmi.payment_type = 'депозит' and coalesce(ig.interval_invoice_corrected, 0) + coalesce(corr.correction, 0) - lg.interval_sale < 0 
                         then pmi.deposit_average_value - (coalesce(ig.interval_invoice_corrected, 0) + coalesce(corr.correction, 0) - lg.interval_sale)
    			  	 else lg.interval_sale - coalesce(ig.interval_invoice_corrected, 0) 
    			end
    	end as new_invoice_amount
    	,'вся история: лиды' as txt_total_leads
    	,lg.total_cnt
    	,lg.total_purchase
    	,lg.total_sale
    	,'вся история: счета' as total_invoices
    	,coalesce(ig.total_invoice, 0) + coalesce(corr.correction, 0) as total_invoice
    	,coalesce(ig.total_receipt, 0) + coalesce(corr.correction, 0) as total_receipt
    	,ig.total_max_invoice_dt
    	,'вся история: счета - лиды' as txt_total_invoice
    	,coalesce(ig.total_invoice, 0) + coalesce(corr.correction, 0) - lg.total_sale as total_leads_minus_invoices
    	,case when pmi.payment_type = 'депозит' then coalesce(ig.total_invoice_corrected, 0) + coalesce(corr.correction, 0) - lg.total_sale else 0 
    	end as total_deposit_balance
    	,'проверка необходимости выставления счетов' txt_check
    	,lg.prev_cnt
    	,lg.prev_purchase
    	,lg.prev_sale
    	,coalesce(ig.curr_invoice, 0) as curr_invoice
    	,coalesce(ig.curr_receipt, 0) as curr_receipt
    	,ig.curr_max_invoice_dt
    	,lg.last_lead_dttm as last_lead_dttm
    	,'техническая информация' as txt_comment
    	,pmi.comment
    	,p.partner_id
    	,p.contract_id
    	,p.contract_number 
    	,p.currency_id
    	,p.organization_id
    	,p.organization_name
    	,p.organization_inn
    	,p.manager_key
    	,p.individual_number
    	,p.individual_description
    from leads_groupped lg
    left join invoices_groupped ig on lg.inn = ig.inn and lg.city_invoice = ig.city_invoice and lg.source_invoice = ig.source_invoice
    left join partners p on lg.inn = p.inn and lg.city_invoice = p.city_invoice
    left join j28046070_sandbox.view_payment_method as pmi on lg.inn = pmi.inn
    left join j28046070_sandbox.deposit_corrections as corr on lg.inn = corr.inn and lg.city_invoice = corr.city_invoice and lg.source_invoice = corr.source_invoice
    """

    mysql_update_view_with_retry(
        db_user=DB_SUPER_USER,
        db_password=DB_SUPER_PASSWORD,
        db_host=DB_HOST,
        db_port=DB_PORT,
        db_dbname='j28046070_leads',
        tbl_name=TBL_NAME,
        tbl_db=TBL_DB,
        query=QUERY,
        big_query_flag=True,
        analyze_tables=ANALYZE_TABLES,
        max_retries=MAX_RETRIES,
        retry_sleep_seconds=RETRY_SLEEP_SECONDS
    )


    ########################################################################################################################
    TBL_DB = 'j28046070_sandbox'
    TBL_NAME = 'view_new_invoices'
    ANALYZE_TABLES = ['j28046070_sandbox.view_invoice_report']
    QUERY = f"""insert into {TBL_DB}.{TBL_NAME}
    select inn, project, legal_entity, city_invoice, source_invoice
        ,payment_type, deposit_min_value, deposit_average_value
        ,interval_cnt, interval_purchase, interval_sale, interval_invoice, interval_receipt, interval_correction, interval_leads_minus_invoices, interval_deposit_balance
        ,new_invoice_flag, new_invoice_description, new_invoice_amount
        ,partner_id, contract_id, organization_id, manager_key
    from j28046070_sandbox.view_invoice_report
    where new_invoice_flag = 'Да'
    and project = 'Даша'
    and inn != '7840087426'
    and partner_id is not null 
    and contract_id is not null
    """

    mysql_update_view_with_retry(
        db_user=DB_SUPER_USER,
        db_password=DB_SUPER_PASSWORD,
        db_host=DB_HOST,
        db_port=DB_PORT,
        db_dbname='j28046070_leads',
        tbl_name=TBL_NAME,
        tbl_db=TBL_DB,
        query=QUERY,
        big_query_flag=True,
        truncate=True,
        analyze_tables=ANALYZE_TABLES,
        max_retries=MAX_RETRIES,
        retry_sleep_seconds=RETRY_SLEEP_SECONDS
    )