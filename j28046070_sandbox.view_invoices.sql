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
		  when p.partner_inn = '0300032821' and i.invoice_comment = 'Алматы' then 'Алматы'
		  when p.partner_inn = '0300032821' and i.invoice_comment != 'Алматы' then 'Улан-Удэ'
          else '' end as city_invoice
	,case when p.partner_inn in ('5047309883','7733331140','7733467800','9701285618','9703181910','9713010350') then 
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
    ,case when p.partner_inn = '760212666248' then '761107378757'
		  when p.partner_inn = '8603207842'   then '7813189404'
          else p.partner_inn
    end as partner_inn
    ,p.partner_type
    ,i.invoice_amount
    ,coalesce(r.receipt_amount, 0) as receipt_amount
    ,r.receipt_dt
    ,case when coalesce(r.receipt_amount, 0) = 0 then 'Не оплачен'
          when r.receipt_amount > 0 AND r.receipt_amount < i.invoice_amount then 'Оплачен частично'
          when r.receipt_amount = i.invoice_amount then 'Оплачен'
          when r.receipt_amount > i.invoice_amount then 'Оплата больше счета'
          else '!!!ERROR!!!' end as invoice_payment_status
    ,i.partner_id
from j28046070_sandbox.invoice_1c i
left join invoice_nomenclature n on i.invoice_id = n.invoice_id
left join receipts_gr r on i.invoice_id = r.invoice_id
left join j28046070_sandbox.organizations_1c o on i.organization_id = o.organization_id
left join j28046070_sandbox.partners_1c p on i.partner_id = p.partner_id