select * from orion.tsb;

select ns, ksb, lgn, ldata, mtype.itsb as mtype, mtype.ktsb,
messages.kuoo, text(ts.nsch) || text(ts.nkts) as codes,
	(select isch from orion.tsch where ts.nsch=tsch.nsch) || ':' || ts.kikts as sender,
messages.kuopr,	text(tb.nsch) || text(tb.nkts) as codeb,
	(select isch from orion.tsch where tb.nsch=tsch.nsch) || ':' || tb.kikts as _before,
messages.kuo, 	text(tn.nsch) || text(tn.nkts) as code, 
	(select isch from orion.tsch where tn.nsch=tsch.nsch) || ':' || tn.kikts as node,
messages.kuosl, text(ta.nsch) || text(ta.nkts) as codea, 
	(select isch from orion.tsch where ta.nsch=tsch.nsch) || ':' || ta.kikts as _after,
messages.kuop, 	text(tr.nsch) || text(tr.nkts) as coder, 
	(select isch from orion.tsch where tr.nsch=tsch.nsch) || ':' || tr.kikts as receiver,
case when messages.kvt1=0 and messages.kvt2 not in (0,1) then 'РС' 
	 when messages.kvt1=1 and messages.dtosb is null and messages.kvt2 not in (0,1) then 'ИС'
	 when messages.kvt1=1 and messages.dtosb is not null and messages.kvt2=0 then 'РС'
	 when messages.kvt1=1 and messages.dtosb is not null and messages.kvt2=1 then 'OK'
	 else 'ИС'
	 end as error,
text(messages.kvt1) || text(messages.kvt2) as kvt, messages.dtosb
from orion.tsb as messages
inner join orion.ttsb as mtype on mtype.ktsb=messages.ktsb
left outer join orion.tuo as tn on tn.kuo=messages.kuo
left outer join orion.tuo as ts on ts.kuo=messages.kuoo
left outer join orion.tuo as tr on tr.kuo=messages.kuop
left outer join orion.tuo as tb on tb.kuo=messages.kuopr
left outer join orion.tuo as ta on ta.kuo=messages.kuosl
--where tn.nsch=1 and tn.nkts=0
where ns=11000
order by ns,ksb
;

--select distinct ns, count(*) as cnt from orion.tsb group by ns order by cnt desc,ns;

===============

select ns, ksb,
messages.kuoo, 	text(ts.nsch) || text(ts.nkts) as codes,
	(select isch from orion.tsch where ts.nsch=tsch.nsch) || ':' || ts.kikts as sender,
messages.kuop, 	text(tb.nsch) || text(tb.nkts) as codeb,
	(select isch from orion.tsch where tb.nsch=tsch.nsch) || ':' || tb.kikts as _before,
messages.kuo, 	text(tn.nsch) || text(tn.nkts) as code, 
	(select isch from orion.tsch where tn.nsch=tsch.nsch) || ':' || tn.kikts as node,
messages.kuopr, text(ta.nsch) || text(ta.nkts) as codea, 
	(select isch from orion.tsch where ta.nsch=tsch.nsch) || ':' || ta.kikts as _after,
messages.kuoo, 	text(tr.nsch) || text(tr.nkts) as coder, 
	(select isch from orion.tsch where tr.nsch=tsch.nsch) || ':' || tr.kikts as receiver,
case when messages.kvt1=0 and messages.kvt2 not in (0,1) then 'РС' 
	 when messages.kvt1=1 and messages.dtosb is null and messages.kvt2 not in (0,1) then 'ИС'
	 when messages.kvt1=1 and messages.dtosb is not null and messages.kvt2=0 then 'РС'
	 when messages.kvt1=1 and messages.dtosb is not null and messages.kvt2=1 then 'OK'
	 else 'ИС'
	 end as error,
text(messages.kvt1) || text(messages.kvt2) as kvt, messages.dtosb
from orion.tsb as messages
left outer join orion.tuo as tn on tn.kuo=messages.kuo
left outer join orion.tuo as ts on ts.kuo=messages.kuoo
left outer join orion.tuo as tr on tr.kuo=messages.kuop
left outer join orion.tuo as tb on tb.kuo=messages.kuopr
left outer join orion.tuo as ta on ta.kuo=messages.kuosl
--where tn.nsch=1 and tn.nkts=0
order by ns
;

--select ns, count(*) from orion.tsb group by ns order by ns;

------------

select ns, ksb,
messages.kuoo, 	text(ts.nsch) || text(ts.nkts) as codes,
	(select isch from orion.tsch where ts.nsch=tsch.nsch) || ':' || ts.kikts as sender,
messages.kuop, 	text(tb.nsch) || text(tb.nkts) as codeb,
	(select isch from orion.tsch where tb.nsch=tsch.nsch) || ':' || tb.kikts as _before,
messages.kuo, 	text(tn.nsch) || text(tn.nkts) as code, 
	(select isch from orion.tsch where tn.nsch=tsch.nsch) || ':' || tn.kikts as node,
messages.kuopr, text(ta.nsch) || text(ta.nkts) as codea, 
	(select isch from orion.tsch where ta.nsch=tsch.nsch) || ':' || ta.kikts as _after,
messages.kuoo, 	text(tr.nsch) || text(tr.nkts) as coder, 
	(select isch from orion.tsch where tr.nsch=tsch.nsch) || ':' || tr.kikts as receiver,
case when messages.kvt1=0 and messages.kvt2 not in (0,1) then 'РС' 
	 when messages.kvt1=1 and messages.dtosb is null and messages.kvt2 not in (0,1) then 'ИС'
	 when messages.kvt1=1 and messages.dtosb is not null and messages.kvt2=0 then 'РС'
	 when messages.kvt1=1 and messages.dtosb is not null and messages.kvt2=1 then 'OK'
	 else 'ИС'
	 end as error,
text(messages.kvt1) || text(messages.kvt2) as kvt, messages.dtosb
from orion.tsb as messages
inner join orion.tuo as tn on tn.kuo=messages.kuo
inner join orion.tuo as ts on ts.kuo=messages.kuoo
inner join orion.tuo as tr on tr.kuo=messages.kuop
inner join orion.tuo as tb on tb.kuo=messages.kuopr
inner join orion.tuo as ta on ta.kuo=messages.kuosl
where tn.nsch=1 and tn.nkts=0
order by ns, ksb
;

-------------

select ns, ksb,
messages.kuo, 	text(tn.nsch) || text(tn.nkts) as node, 
	(select isch from orion.tsch where tn.nsch=tsch.nsch) || ':' || tn.kikts as node,
messages.kuoo, 	text(ts.nsch) || text(ts.nkts) as nodes, 
	(select isch from orion.tsch where ts.nsch=tsch.nsch) || ':' || ts.kikts as sender,
messages.kuop, 	text(tb.nsch) || text(tb.nkts) as nodeb, 
	(select isch from orion.tsch where tb.nsch=tsch.nsch) || ':' || tb.kikts as _before,
messages.kuoo, 	text(tr.nsch) || text(tr.nkts) as noder, 
	(select isch from orion.tsch where tr.nsch=tsch.nsch) || ':' || tr.kikts as receiver,
messages.kuopr, text(ta.nsch) || text(ta.nkts) as nodea, 
	(select isch from orion.tsch where ta.nsch=tsch.nsch) || ':' || ta.kikts as _after

from orion.tsb as messages
inner join orion.tuo as tn on tn.kuo=messages.kuo
inner join orion.tuo as ts on ts.kuo=messages.kuoo
inner join orion.tuo as tr on tr.kuo=messages.kuop
inner join orion.tuo as tb on tb.kuo=messages.kuopr
inner join orion.tuo as ta on ta.kuo=messages.kuosl
where tn.nsch=1 and tn.nkts=0
order by ns, ksb
;

==============

        select ksb, messagetypes.itsb as messagetype, 
        (
            select division.isch || ':' || kikts
            from orion.tuo as node inner join orion.tsch as division on division.nsch=node.nsch
            where node.kuo=messages.kuo
        ) as node,
        (
            select division.isch || ':' || kikts
            from orion.tuo as node inner join orion.tsch as division on division.nsch=node.nsch
            where node.kuo=messages.kuoo
        ) as sender,
        (
            select division.isch || ':' || kikts
            from orion.tuo as node inner join orion.tsch as division on division.nsch=node.nsch
            where node.kuo=messages.kuop
        ) as receiver,
        (
            select division.isch || ':' || kikts
            from orion.tuo as node inner join orion.tsch as division on division.nsch=node.nsch
            where node.kuo=messages.kuopr
        ) as previousnode,
        (
            select division.isch || ':' || kikts
            from orion.tuo as node inner join orion.tsch as division on division.nsch=node.nsch
            where node.kuo=messages.kuosl
        ) as nextnode,
        kuo, kuoo, kuop, kuopr, kuosl,
        ns, lgn, messages.ktsb, ldata, dtosb, dtpsb,
        kvt1, dtokvt1, kvt2, dtpkvt2
        from orion.tsb as messages
        inner join orion.ttsb as messagetypes on messagetypes.ktsb=messages.ktsb
        order by messages.dtpsb desc

--------------

        select ksb, messagetypes.itsb as messagetype, 
        (
            select division.isch || ':' || kikts
            from orion.tuo as node inner join orion.tsch as division on division.nsch=node.nsch
            where node.kuo=messages.kuo
        ) as node,
        (
            select division.isch || ':' || kikts
            from orion.tuo as node inner join orion.tsch as division on division.nsch=node.nsch
            where node.kuo=messages.kuoo
        ) as sender,
        (
            select division.isch || ':' || kikts
            from orion.tuo as node inner join orion.tsch as division on division.nsch=node.nsch
            where node.kuo=messages.kuop
        ) as receiver,
        (
            select division.isch || ':' || kikts
            from orion.tuo as node inner join orion.tsch as division on division.nsch=node.nsch
            where node.kuo=messages.kuopr
        ) as previousnode,
        (
            select division.isch || ':' || kikts
            from orion.tuo as node inner join orion.tsch as division on division.nsch=node.nsch
            where node.kuo=messages.kuosl
        ) as nextnode,
        kuo, kuoo, kuop, kuopr, kuosl,
        ns, lgn, messages.ktsb, ldata, dtosb, dtpsb,
        kvt1, dtokvt1, kvt2, dtpkvt2
        from orion.tsb as messages
        inner join orion.ttsb as messagetypes on messagetypes.ktsb=messages.ktsb
        order by messages.dtpsb desc

----------------

        select ksb, messagetypes.itsb as messagetype, 
            kuo, kuoo, kuop, kuopr, kuosl,
            ns, lgn, messages.ktsb, ldata, dtosb, dtpsb,
            kvt1, dtokvt1, kvt2, dtpkvt2,
        (
            select division.isch || ':' || kikts
            from orion.tuo as node inner join orion.tsch as division on division.nsch=node.nsch
            where node.kuo=messages.kuo
        ) as node,
        (
            select division.isch || ':' || kikts
            from orion.tuo as node inner join orion.tsch as division on division.nsch=node.nsch
            where node.kuo=messages.kuoo
        ) as sender,
        (
            select division.isch || ':' || kikts
            from orion.tuo as node inner join orion.tsch as division on division.nsch=node.nsch
            where node.kuo=messages.kuop
        ) as receiver,
        (
            select division.isch || ':' || kikts
            from orion.tuo as node inner join orion.tsch as division on division.nsch=node.nsch
            where node.kuo=messages.kuopr
        ) as previousnode,
        (
            select division.isch || ':' || kikts
            from orion.tuo as node inner join orion.tsch as division on division.nsch=node.nsch
            where node.kuo=messages.kuosl
        ) as nextnode
        from orion.tsb as messages
        inner join orion.ttsb as messagetypes on messagetypes.ktsb=messages.ktsb
        order by messages.dtpsb desc
