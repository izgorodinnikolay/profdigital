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
	select project, legal_entity, inn, stop_flg, payment_type, deposit_min_value, deposit_average_value, comment
	from inn_from_google
	union all
	select
	    'нет инфо' as project,
	    legalEntity as legal_entity,
	    inn AS inn,
		null as stop_flg,
	    'постоплата. еженедельно' as payment_type,
	    0 AS deposit_min_value,
	    0 AS deposit_average_value,
	    'Заполнить Google таблицу' as comment
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
select i.project, i.legal_entity, i.inn, i.stop_flg, i.payment_type, i.deposit_min_value, i.deposit_average_value, i.comment
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
from inn_all i cross join dt