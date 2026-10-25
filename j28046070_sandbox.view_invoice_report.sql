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
-- 				order by case when o.organization_inn = '720307197077' then 1 else 0 end desc, partner_name
				order by partner_name
				) rn
		from j28046070_sandbox.partners_1c p
		join j28046070_sandbox.contract_1c c on p.partner_id = c.partner_id 
		join j28046070_sandbox.organizations_1c o on c.organization_id = o.organization_id
		join j28046070_sandbox.individuals_1c i on o.manager_key = i.individual_id
		where 1=1
		and c.is_deleted = 0
		and c.description = 'Ведение платного трафика'
		and (   o.organization_inn = '720307197077'
--		    or (p.partner_inn = '7707458687' and o.organization_inn = '503013732480')
		    )
		) t
	where rn = 1
)
select lg.inn, pmi.project, pmi.stop_flg, coalesce(p.partner_name, pmi.legal_entity) as legal_entity, lg.city_invoice
	,coalesce(pm.comment, '') as pm_comment
	,lg.source_invoice
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
	,coalesce(ig.interval_invoice_corrected, 0) + coalesce(corr.correction, 0) - coalesce(lg.interval_sale, 0) as interval_invoices_minus_leads
	,case when lg.inn in ('7840087426', '720306065102')
			or lg.prev_cnt = 0 
			or ig.curr_invoice > 0 
			or (	pmi.payment_type = 'депозит' 
				and coalesce(ig.interval_invoice_corrected, 0) + coalesce(corr.correction, 0) - coalesce(lg.interval_sale, 0) > pmi.deposit_min_value
				)
			or p.partner_id is null
			or p.contract_id is null
			or project = 'нет инфо'
		  then 'Нет'
		  else 'Да'
	end as new_invoice_flag
	,case when lg.inn in ('7840087426', '720306065102')
			then 'Не выставляю счета по этому клиенту'
		  when lg.prev_cnt = 0 
			then 'Нет лидов за предыдущий период'
		  when ig.curr_invoice > 0 
		  	then 'В текущем периоде счет уже выставлен'
		  when  pmi.payment_type = 'депозит' 
		  	and coalesce(ig.interval_invoice_corrected, 0) + coalesce(corr.correction, 0) - coalesce(lg.interval_sale, 0) > pmi.deposit_min_value
		  	then 'Остаток больше мин депозита'
		  when p.partner_id is null or p.contract_id is null 
		  	then 'Заполнить данные в 1С'
		  when project = 'нет инфо'
		  	then 'В google таблице нет инфо по ИНН'
		  	else ''
	end as new_invoice_description_short
	,case when lg.inn in ('7840087426', '720306065102')
			then concat(coalesce(p.partner_name, pmi.legal_entity), ', ИНН ', lg.inn, ' - не выставляю счета по этому клиенту')
		  when lg.prev_cnt = 0 
			then concat('Нет лидов с ', 
						date_format(pmi.leads_prev_start, '%%Y-%%m-%%d'), 
						' по ', 
						date_format(pmi.leads_prev_end, '%%Y-%%m-%%d')
						)
		  when ig.curr_invoice > 0 
		  	then concat('C ', 
		  				date_format(pmi.invoice_curr_start, '%%Y-%%m-%%d'), 
		  				' по ', 
		  				date_format(pmi.invoice_curr_end, '%%Y-%%m-%%d'), 
		  				' уже выставлен счет на ',
		  				REPLACE(REPLACE(FORMAT(ig.curr_invoice, 0, 'en_US'), ',', ' '), '.', '.')
		  				)
		  when pmi.payment_type = 'депозит' 
		    and coalesce(ig.interval_invoice_corrected, 0) + coalesce(corr.correction, 0) - coalesce(lg.interval_sale, 0) > pmi.deposit_min_value 
		  	then concat('Остаток (', 
		  				REPLACE(REPLACE(FORMAT(coalesce(ig.interval_invoice_corrected, 0) + coalesce(corr.correction, 0) - coalesce(lg.interval_sale, 0), 0, 'en_US'), ',', ' '), '.', '.'),
		  				') больше мин депозита (',
		  				REPLACE(REPLACE(FORMAT(pmi.deposit_min_value, 0, 'en_US'), ',', ' '), '.', '.'), 
		  				')'
		  				)
		  when p.partner_id is null 
		  	then concat('По ИНН ', lg.inn, ' в 1С отсутствуют данные в Catalog_Контрагенты')
		  when p.contract_id is null 
		  	then concat('По ИНН ', lg.inn, ' в 1С отсутствуют данные в Catalog_ДоговорыКонтрагентов')
		  when project = 'нет инфо'
		  	then concat('В google таблице нет инфо по ИНН ', lg.inn)
		  	else ''
	end as new_invoice_description_long
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
	,case when lg.inn in ('7840087426', '720306065102') then ''
		  when lg.prev_cnt > 0 and lg.interval_sale > 0 and pmi.project = 'нет инфо'
			then 'Нет инфо в google таблице'
		  when lg.prev_cnt > 0 and lg.interval_sale > 0 and pmi.project != 'нет инфо' and (p.partner_id is null or p.contract_id is null)
		  	then concat('В 1С не заполнены: ', 
		  				case when p.partner_id is null then 'Catalog_Контрагенты ' else ' ' end,
		  				case when p.contract_id is null then 'Catalog_ДоговорыКонтрагентов' else ' ' end
		  				)
		  when lg.interval_sale > 0 and pmi.project != 'нет инфо' and ig.curr_invoice > 0
		  	and coalesce(ig.interval_invoice_corrected, 0) + coalesce(corr.correction, 0) - coalesce(lg.interval_sale, 0) < pmi.deposit_min_value
			then concat('Счет на ',
						REPLACE(REPLACE(FORMAT(ig.curr_invoice, 0, 'en_US'), ',', ' '), '.', '.'), 
						', но текущий баланс ',
						REPLACE(REPLACE(FORMAT(coalesce(ig.interval_invoice_corrected, 0) + coalesce(corr.correction, 0) - coalesce(lg.interval_sale, 0), 0, 'en_US'), ',', ' '), '.', '.')
						)
			else ''
	end as new_invoice_errors
	,'вся история: лиды' as txt_total_leads
	,lg.total_cnt
	,lg.total_purchase
	,lg.total_sale
	,'вся история: счета' as total_invoices
	,coalesce(ig.total_invoice, 0) + coalesce(corr.correction, 0) as total_invoice
	,coalesce(ig.total_receipt, 0) + coalesce(corr.correction, 0) as total_receipt
	,ig.total_max_invoice_dt
	,'вся история: счета - лиды' as txt_total_invoice
	,coalesce(ig.total_invoice, 0) + coalesce(corr.correction, 0) - lg.total_sale as total_invoices_minus_leads
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
left join partners p on lg.inn = p.inn and (lg.city_invoice = p.city_invoice or lg.inn = '0300032821')
left join j28046070_sandbox.view_payment_method as pmi on lg.inn = pmi.inn
left join j28046070_sandbox.deposit_corrections as corr on lg.inn = corr.inn and lg.city_invoice = corr.city_invoice and lg.source_invoice = corr.source_invoice
left join j28046070_sandbox.pm_corrections as pm on lg.inn = pm.inn and lg.city_invoice = pm.city_invoice and lg.source_invoice = pm.source_invoice