--speeds with errors
select node, nodes.kikts as line,
	sum(s1+s2) as volume,
	round(cast(float8 (sum(dtime) ) as numeric), 2) as time,
	round(cast(float8 (sum(s1+s2) / sum(dtime) / 60) as numeric),2) as speed,
	sum(errors) as errors
from
(
 (select kuop as node, dtpsb, dtosb, sum(ldata) as s1, 0 as s2,
  abs(EXTRACT(EPOCH FROM dtpsb::timestamp-dtosb::timestamp)) as dtime,
  sum(case when kvt1=0 then 1 else 0 end) as errors
  from orion.tsb
  where kuop is not null and kuoo is not null and kuo=2 and dtosb is not null and dtpsb is not null
  group by kuop, dtpsb, dtosb)
  union
 (select kuoo as node, dtpsb, dtosb, 0 as s1, sum(ldata) as s2,
  abs(EXTRACT(EPOCH FROM dtpsb::timestamp-dtosb::timestamp)) as dtime,
  sum(case when kvt2=0 then 1 else 0 end) as errors
  from orion.tsb
  where kuoo is not null and kuop is not null and kuo=2 and dtosb is not null and dtpsb is not null
  group by kuoo, dtpsb, dtosb)
) as capacities
 inner join orion.tuo as nodes on capacities.node=nodes.kuo
 group by node, line
 order by node, line;

===========

(select kuop as node, dtpsb, dtosb, ldata as s1, 0 as s2,
  abs(EXTRACT(EPOCH FROM dtpsb::timestamp-dtosb::timestamp)) as dtime,
  COALESCE(kvt1, -1) as kvt1, 
  COALESCE(kvt2, -1) as kvt2
  from orion.tsb
  where kuop is not null and kuoo is not null and kuo=2 and dtosb is not null and dtpsb is not null and
 	(kvt1 != 1 or kvt2 != 1)
  --group by kuopr, dtpsb, dtosb
);

--select * from orion.tsb where kvt1 != 1 or kvt2 != 1;

------------

--speeds with errors
select node, nodes.kikts as line,
	sum(s1+s2) as volume,
	round(cast(float8 (sum(dtime) ) as numeric), 2) as time,
	round(cast(float8 (sum(s1+s2) / sum(dtime) / 60) as numeric),2) as speed,
	sum(errors) as errors
from
(
 (select kuop as node, dtpsb, dtosb, sum(ldata) as s1, 0 as s2,
  abs(EXTRACT(EPOCH FROM dtpsb::timestamp-dtosb::timestamp)) as dtime,
  sum(case when kvt1=0 or kvt2=0 then 1 else 0 end) as errors
  from orion.tsb
  where kuop is not null and kuoo is not null and kuo=2 and dtosb is not null and dtpsb is not null
  group by kuop, dtpsb, dtosb)
  union
 (select kuoo as node, dtpsb, dtosb, 0 as s1, sum(ldata) as s2,
  abs(EXTRACT(EPOCH FROM dtpsb::timestamp-dtosb::timestamp)) as dtime,
  sum(case when kvt1=0 or kvt2=0 then 1 else 0 end) as errors
  from orion.tsb
  where kuoo is not null and kuop is not null and kuo=2 and dtosb is not null and dtpsb is not null
  group by kuoo, dtpsb, dtosb)
) as capacities
 inner join orion.tuo as nodes on capacities.node=nodes.kuo
 group by node, line
 order by node, line;

=============

select node, nodes.kikts as line,
	sum(s1+s2) as volume,
	round(cast(float8 (sum(dtime) / 60 ) as numeric), 2) as time,
	round(cast(float8 (sum(s1+s2) / sum(dtime) / 60) as numeric),2) as speed
from
(
 (select kuop as node, dtpsb, dtosb, sum(ldata) as s1, 0 as s2,
  abs(EXTRACT(EPOCH FROM dtpsb::timestamp-dtosb::timestamp)) as dtime
  from orion.tsb
  where kuop is not null and kuoo is not null and kuo=2 and dtosb is not null and dtpsb is not null
  group by kuop, dtpsb, dtosb)
  union
 (select kuoo as node, dtpsb, dtosb, 0 as s1, sum(ldata) as s2,
  abs(EXTRACT(EPOCH FROM dtpsb::timestamp-dtosb::timestamp)) as dtime
  from orion.tsb
  where kuoo is not null and kuop is not null and kuo=2 and dtosb is not null and dtpsb is not null
  group by kuoo, dtpsb, dtosb)
) as capacities
 inner join orion.tuo as nodes on capacities.node=nodes.kuo
 group by node, line
 order by node, line;

--test data
============

(select kuop as node, dtpsb, dtosb, ldata as s1, 0 as s2,
  abs(EXTRACT(EPOCH FROM dtpsb::timestamp-dtosb::timestamp)) as dtime
  from orion.tsb
  where kuop is not null and kuoo is not null and kuo=2 and dtosb is not null and dtpsb is not null
  --group by kuop, dtpsb, dtosb
)

=========== 

select node, nodes.kikts as line,
	sum(s1+s2) as volume,
	round(cast(float8 (sum(dtime) /60 ) as numeric), 2) as time,
	round(cast(float8 (sum(s1+s2) / sum(dtime) / 60) as numeric),2) as speed
from
(
 (select kuopr as node, dtpsb, dtosb, sum(ldata) as s1, 0 as s2,
  abs(EXTRACT(EPOCH FROM dtpsb::timestamp-dtosb::timestamp)) as dtime
  from orion.tsb
  where kuopr is not null and kuosl is not null and kuo=2 and dtosb is not null and dtpsb is not null
  group by kuopr, dtpsb, dtosb)
  union
 (select kuosl as node, dtpsb, dtosb, 0 as s1, sum(ldata) as s2,
  abs(EXTRACT(EPOCH FROM dtpsb::timestamp-dtosb::timestamp)) as dtime
  from orion.tsb
  where kuopr is not null and kuosl is not null and kuo=2 and dtosb is not null and dtpsb is not null
  group by kuosl, dtpsb, dtosb)
) as capacities
 inner join orion.tuo as nodes on capacities.node=nodes.kuo
 group by node, line
 order by node, line;

--------

select node, nodes.kikts as line,
	sum(s1+s2) as volume,
	sum(dtime),
	round(cast(float8 (sum(s1+s2) / sum(dtime) / 60) as numeric),2) as speed
from
(
 (select kuopr as node, dtpsb, dtosb, sum(ldata) as s1, 0 as s2,
  abs(EXTRACT(EPOCH FROM dtpsb::timestamp-dtosb::timestamp)) as dtime
  from orion.tsb
  where kuopr is not null and kuosl is not null and kuo=2 and dtosb is not null and dtpsb is not null
  group by kuopr, dtpsb, dtosb)
  union
 (select kuosl as node, dtpsb, dtosb, 0 as s1, sum(ldata) as s2,
  abs(EXTRACT(EPOCH FROM dtpsb::timestamp-dtosb::timestamp)) as dtime
  from orion.tsb
  where kuopr is not null and kuosl is not null and kuo=2 and dtosb is not null and dtpsb is not null
  group by kuosl, dtpsb, dtosb)
) as capacities
 inner join orion.tuo as nodes on capacities.node=nodes.kuo
 group by node, line
 order by node, line;

---------

select * from orion.tsb;

select node, nodes.kikts as line
	sum(s1+s2) as volume,
	round(cast(float8 (sum(s1+s2) / sum(abs(EXTRACT(EPOCH FROM dtpsb::timestamp-dtosb::timestamp))) / 60) as numeric),2) as speed
from
(
 (select kuopr as node, ktsb as mtype, count(*) as c1, sum(ldata) as s1, 0 as c2, 0 as s2 from orion.tsb
  where kuopr is not null and kuosl is not null and kuo=2 and dtosb is not null and dtpsb is not null
  group by kuopr, ktsb)
  union
 (select kuosl as node, ktsb as mtype, 0 as c1, 0 as s1, count(*) as c2, sum(ldata) as s2 from orion.tsb
  where kuopr is not null and kuosl is not null and kuo=2 and dtosb is not null and dtpsb is not null
  group by kuosl, ktsb)
) as capacities
 inner join orion.tuo as nodes on capacities.node=nodes.kuo
 inner join orion.ttsb as messagetypes on capacities.mtype=messagetypes.ktsb
 group by node, mtype, line, ktsb, messagetype
 order by node, mtype, line, ktsb, messagetype

----------

select
round(cast(float8 (sum(ldata) / sum(abs(EXTRACT(EPOCH FROM dtpsb::timestamp-dtosb::timestamp))) / 60) as numeric),2) as speed
from orion.tsb where dtosb is not null;

select * from orion.tsb;