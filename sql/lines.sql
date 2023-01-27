
select ksd, kuo, kuov, 
	case when kuo is null then '' else kuo::text end || ':' || case when kuov is null then '' else kuov::text end as line,
	ssd from orion.tsd;

---------

select * from orion.tsch;
select nsch, isch, vch from orion.tsch order by nsch;

select * from orion.tsd;
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

----------

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
order by line;
