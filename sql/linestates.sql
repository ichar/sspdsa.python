select distinct line.ksd,
(
	select (select isch from orion.tsch where node.nsch=tsch.nsch) || ':' || kikts
	from orion.tuo as node where node.kuo=line.kuo)
|| ' - ' ||
(
	select (select isch from orion.tsch where node.nsch=tsch.nsch) || ':' || kikts
	from orion.tuo as node where node.kuo=line.kuov) as line
from orion.tvsd as linestate
inner join orion.tsd as line on line.ksd=linestate.ksd 
where (kuo is not null and kuov is not null) and (kuo=2 or kuov=2)
order by line.ksd;

-------------

select distinct line.ksd,
(
	select (select isch from orion.tsch where node.nsch=tsch.nsch) || ':' || kikts
	from orion.tuo as node where node.kuo=line.kuo)
|| ' - ' ||
(
	select (select isch from orion.tsch where node.nsch=tsch.nsch) || ':' || kikts
	from orion.tuo as node where node.kuo=line.kuov) as line
from orion.tvsd as linestate
inner join orion.tsd as line on line.ksd=linestate.ksd 
where kuo is not null and kuov is not null
order by line.ksd;

-------------------

select dtsd as date, linestate.ksd, prvsd, kuo, kuov, ssd,
(
	select division.isch || ':' || kikts
	from orion.tuo as node inner join orion.tsch as division on division.nsch=node.nsch
	where node.kuo=line.kuo
) as node1,
(
	select division.isch || ':' || kikts
	from orion.tuo as node inner join orion.tsch as division on division.nsch=node.nsch
	where node.kuo=line.kuov
) as node2
from orion.tvsd as linestate
inner join orion.tsd as line on line.ksd=linestate.ksd
where kuo is not null and kuov is not null and 
	(dtsd > '2022-11-14 00:00:00' and dtsd < '2022-11-14 23:59:59') and linestate.ksd = 10
order by ksd, kuo, kuov, date;

--select distinct ksd from orion.tvsd order by ksd;

select dtsd as date, linestate.ksd, prvsd, kuo, kuov, ssd,
(
	select division.isch || ':' || kikts
	from orion.tuo as node inner join orion.tsch as division on division.nsch=node.nsch
	where node.kuo=line.kuo
) as node1,
(
	select division.isch || ':' || kikts
	from orion.tuo as node inner join orion.tsch as division on division.nsch=node.nsch
	where node.kuo=line.kuov
) as node2,
(
	select node.nsch || '_' || node.nsch || nkts
	from orion.tuo as node inner join orion.tsch as division on division.nsch=node.nsch
	where node.kuo=line.kuo
) || '-' ||
(
	select node.nsch || '_' || node.nsch || nkts
	from orion.tuo as node inner join orion.tsch as division on division.nsch=node.nsch
	where node.kuo=line.kuov
	) as code

from orion.tvsd as linestate
inner join orion.tsd as line on line.ksd=linestate.ksd
where kuo is not null and kuov is not null and 
	(dtsd > '2022-11-14 00:00:00' and dtsd < '2022-11-14 23:59:59') and linestate.ksd = 10
order by ksd, kuo, kuov, date;

----------

select kuo, uruo, nsch, nkts, 
	case when kikts='КПТС-О' then kikts || ' ' || nsch::text else kikts end,
	nsch::text||nkts::text as Node  from orion.tuo order by uruo, nsch, nkts;

select ksd, kuo, kuov, 
	case when kuo is null then '' else kuo::text end || ':' || case when kuov is null then '' else kuov::text end as line,
	ssd from orion.tsd;

select min(dtsd), max(dtsd) from orion.tvsd;
select distinct to_char(dtsd, 'YYYY-MM-DD HH:MI') as date, kvsd, ksd, prvsd from orion.tvsd order by date desc;
select * from orion.tvsd order by dtsd desc;

select distinct to_char(dtsd, 'YYYY-MM-DD HH:MI') as date, 
	linestate.ksd, prvsd, kuo, kuov, ssd,
	(
		select (select isch from orion.tsch where node.nsch=tsch.nsch) || ':' || kikts
		from orion.tuo as node where node.kuo=line.kuo) as node1,
	(
		select (select isch from orion.tsch where node.nsch=tsch.nsch) || ':' || kikts
		from orion.tuo as node where node.kuo=line.kuov) as node2
	from orion.tvsd as linestate
	inner join orion.tsd as line on line.ksd=linestate.ksd 
order by date desc;

----------

select dtsd as date, linestate.ksd, kuo, kuov, ssd,
	(
		select (select isch from orion.tsch where node.nsch=tsch.nsch) || ':' || kikts
		from orion.tuo as node where node.kuo=line.kuo)
	|| ' - ' ||
	(
		select (select isch from orion.tsch where node.nsch=tsch.nsch) || ':' || kikts
		from orion.tuo as node where node.kuo=line.kuov) as node
	from orion.tvsd as linestate
	inner join orion.tsd as line on line.ksd=linestate.ksd 
order by date desc;

select 
	(
		select (select isch from orion.tsch where node.nsch=tsch.nsch) || ':' || kikts
		from orion.tuo as node where node.kuo=line.kuo)
	|| ' - ' ||
	(
		select (select isch from orion.tsch where node.nsch=tsch.nsch) || ':' || kikts
		from orion.tuo as node where node.kuo=line.kuov) as node,
	dtsd as date, linestate.ksd, prvsd, kuo, kuov, ssd
	from orion.tvsd as linestate
	inner join orion.tsd as line on line.ksd=linestate.ksd 
order by node, date;

----------------

select distinct to_char(dtsd, 'YYYY-MM-DD HH:MI:SS') as date, 
	linestate.ksd, prvsd, kuo, kuov, ssd,
	(
		select (select isch from orion.tsch where node.nsch=tsch.nsch) || ':' || kikts
		from orion.tuo as node where node.kuo=line.kuo)
	|| ' - ' ||
	(
		select (select isch from orion.tsch where node.nsch=tsch.nsch) || ':' || kikts
		from orion.tuo as node where node.kuo=line.kuov) as node
	from orion.tvsd as linestate
	inner join orion.tsd as line on line.ksd=linestate.ksd 
order by date desc;

select dtsd as date, linestate.ksd, prvsd, kuo, kuov, ssd,
(
	select (select isch from orion.tsch where node.nsch=tsch.nsch) || ':' || kikts
	from orion.tuo as node where node.kuo=line.kuo
) as node1,
(
	select (select isch from orion.tsch where node.nsch=tsch.nsch) || ':' || kikts
	from orion.tuo as node where node.kuo=line.kuov
) as node2
from orion.tvsd as linestate
inner join orion.tsd as line on line.ksd=linestate.ksd 
where kuo is not null and kuov is not null
order by kuo, kuov, date;

-------------

select kuo, uruo, nsch, nkts, 
	case when kikts='КПТС-О' then kikts || ' ' || nsch::text else kikts end,
	nsch::text||nkts::text as Node  from orion.tuo order by uruo, nsch, nkts;

select ksd, kuo, kuov, 
	case when kuo is null then '' else kuo::text end || ':' || case when kuov is null then '' else kuov::text end as line,
	ssd from orion.tsd;

select min(dtsd), max(dtsd) from orion.tvsd;
select distinct to_char(dtsd, 'YYYY-MM-DD HH:MI') as date, kvsd, ksd, prvsd from orion.tvsd order by date desc;
select * from orion.tvsd order by dtsd desc;

select distinct to_char(dtsd, 'YYYY-MM-DD HH:MI:SS') as date, 
	linestate.ksd, prvsd, kuo, kuov, ssd,
	(
		select (select isch from orion.tsch where node.nsch=tsch.nsch) || ':' || kikts
		from orion.tuo as node where node.kuo=line.kuo)
	|| ' - ' ||
	(
		select (select isch from orion.tsch where node.nsch=tsch.nsch) || ':' || kikts
		from orion.tuo as node where node.kuo=line.kuov) as node
	from orion.tvsd as linestate
	inner join orion.tsd as line on line.ksd=linestate.ksd 
order by date desc;

select 
	(
		select (select isch from orion.tsch where node.nsch=tsch.nsch) || ':' || kikts
		from orion.tuo as node where node.kuo=line.kuo)
	|| ' - ' ||
	(
		select (select isch from orion.tsch where node.nsch=tsch.nsch) || ':' || kikts
		from orion.tuo as node where node.kuo=line.kuov) as node,
	dtsd as date, linestate.ksd, prvsd, kuo, kuov, ssd
	from orion.tvsd as linestate

	inner join orion.tsd as line on line.ksd=linestate.ksd 
order by node, date;

select min(dtsd), max(dtsd) from orion.tvsd;

select dtsd as date, linestate.ksd, prvsd, kuo, kuov, ssd,
(
	select (select isch from orion.tsch where node.nsch=tsch.nsch) || ':' || kikts
	from orion.tuo as node where node.kuo=line.kuo
) as node1,
(
	select (select isch from orion.tsch where node.nsch=tsch.nsch) || ':' || kikts
	from orion.tuo as node where node.kuo=line.kuov
) as node2
from orion.tvsd as linestate
inner join orion.tsd as line on line.ksd=linestate.ksd 
where kuo is not null and kuov is not null
order by kuo, kuov, date;
