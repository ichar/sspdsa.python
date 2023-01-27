select kuo, nkts, nsch, uruo, kikts from orion.tuo order by kikts;
select * from orion.tuo;
-- Свой УО
select kuo from orion.tuo where nsch=1 and nkts=0;

-------------

select kuo, nkts, nsch, uruo, kikts from orion.tuo order by kikts;
select kuo, nkts, nsch, uruo, kikts from orion.tuo order by nsch, kuo, nkts;

select kuo, uruo, nsch, nkts, 
	case when kikts='КПТС-О' then kikts || ' ' || nsch::text else kikts end,
	nsch::text||nkts::text as Node  from orion.tuo order by uruo, nsch, nkts;
	
select kuo, uruo, nsch, nkts, kikts, pikts, nsch::text||nkts::text as Node  from orion.tuo order by node;

select * from orion.tuo order by kuo;
select kuo, uruo, nsch, nkts, kikts, pikts, suo, nsch::text||nkts::text as Node  from orion.tuo order by node;

select kuo, uruo, nsch, nkts, kikts, pikts, suo, nsch::text||'_'||nsch::text||nkts::text as Node  from orion.tuo order by node;

-----------------------

update  orion.tuo set uruo=1 where nsch=1 and nkts=0;
update  orion.tuo set uruo=2 where nsch=0 and nkts=1;
update  orion.tuo set uruo=2 where nsch=1 and nkts in (1,2,3);
update  orion.tuo set uruo=2 where nsch in (2,3,4,5) and nkts=0;
update  orion.tuo set uruo=3 where nsch in (2,3,4,5) and nkts>0;

-----------------------

update  orion.tuo set uruo=1 where nsch=1 and nkts=0;
update  orion.tuo set uruo=2 where nsch=0 and nkts=1;
update  orion.tuo set uruo=2 where nsch=1 and nkts in (1,2,3);
update  orion.tuo set uruo=2 where nsch in (2,3,4,5) and nkts=0;
update  orion.tuo set uruo=3 where nsch in (2,3,4,5) and nkts>0;