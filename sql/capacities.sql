-- capacities
select node, mtype, nodes.pikts as line, 
  messagetypes.itsb as messagetype, 
  sum(c1)::text||'-'||sum(c2)::text as capacity, 
  sum(s1)::text||'-'||sum(s2)::text as volume 
from
(
 (select kuopr as node, ktsb as mtype, count(*) as c1, 0 as c2, sum(ldata) as s1, 0 as s2 from orion.tsb
  where kuopr is not null and kuo=2
  group by kuopr, ktsb)
  union
 (select kuosl as node, ktsb as mtype, 0 as c1, count(*) as c2, 0 as s1, sum(ldata) as s2 from orion.tsb
  where kuosl is not null and kuo=2
  group by kuosl, ktsb)
) as capacities
 inner join orion.tuo as nodes on capacities.node=nodes.kuo
 inner join orion.ttsb as messagetypes on capacities.mtype=messagetypes.ktsb
 group by node, mtype, line, ktsb, messagetype
 order by node, mtype, line, ktsb, messagetype
;

select * from orion.tts;
select * from orion.ttsb;

==============

select node, nodes.kikts as line, messagetype, sum(c1)::text||'-'||sum(c2)::text as capacity, sum(s1)::text||'-'||sum(s2)::text as volume from
(
 (select kuopr as node, ktsb as messagetype, count(*) as c1, sum(ldata) as s1, 0 as c2, 0 as s2 from orion.tsb
  where kuopr is not null and kuosl is not null and kuo=2
  group by kuopr, ktsb)
  union
 (select kuosl as node, ktsb as messagetype, 0 as c1, 0 as s1, count(*) as c2, sum(ldata) as s2 from orion.tsb
  where kuopr is not null and kuosl is not null and kuo=2
  group by kuosl, ktsb)
) as capacities
 inner join orion.tuo as nodes on capacities.node=nodes.kuo
 group by node, line, messagetype
 order by node, line, messagetype

---------

select node, messagetype, count(*) as capacity, sum(size) as volume from
(
 (select kuopr as node, ktsb as messagetype, ldata as size from orion.tsb
	where kuopr is not null and kuosl is not null and kuo=2)
union
 (select kuosl as node, ktsb as messagetype, ldata as size from orion.tsb
	where kuopr is not null and kuosl is not null and kuo=2)
) as capacities
group by node,messagetype
order by node

-------
		
select * from orion.tsb;

select kuo, ktsb, kuopr, kuosl, count(*) as mtypes, sum(ldata) as volume
from orion.tsb
where kuop is not null and kuosl is not null
group by kuo, ktsb, kuopr, kuosl
order by kuo;
