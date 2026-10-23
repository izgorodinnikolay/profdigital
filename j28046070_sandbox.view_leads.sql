select l.project, l.dateAdd, l.dateTimeAdd
	,DATE_ADD(l.dateAdd, INTERVAL (6 - WEEKDAY(l.dateAdd)) DAY) as week_end
	,case when l.inn = '720307197077' then '2463115644'
          when l.inn = '760212666248' then '761107378757'
		  when l.inn = '8603207842'   then '7813189404'
		  when l.inn = '246207417145' then '246205494401'
	      when length(l.inn) in (9, 11) then concat('0', l.inn) else l.inn end as inn
	,case when l.inn in ('300032821', '2310229806', '3900034752', '4205421649', '7727471830') then l.city else '' end as city_invoice
	,case when l.inn in ('5047309883','7733331140','7733467800','9701285618','9703181910','9713010350') then 
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
from j28046070_leads.leads as l