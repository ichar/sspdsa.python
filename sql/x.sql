--
-- Type for routes note data item
--
DROP TYPE IF EXISTS orion.t_route_note;
CREATE TYPE orion.t_route_note AS (
    is_done boolean,
    node_id bigint,
    code char(2),
    node_name varchar(20),
    sdt timestamp without time zone,
    err smallint
);
--
--  Function to clear route node value
--  ROW (0, null, '', '', null, 0)
--
CREATE OR REPLACE FUNCTION orion.clear_route_node_fn(
    OUT is_done boolean,
    OUT node_id bigint,
    OUT code char(2),
    OUT node_name varchar(20),
    OUT sdt timestamp without time zone,
    OUT err smallint
    ) AS $$
begin
    is_done = 0;
    node_id = null;
    code = '';
    node_name = '';
    sdt = null;
    err = -1;
end
$$LANGUAGE 'plpgsql'
;

--------------

do $$
DECLARE
    l_node1 orion.t_route_note;
BEGIN
    select * into l_node1 from orion.clear_route_node_fn();
	RAISE NOTICE '%', l_node1;
END;
$$

------------

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
	 when messages.kvt1=1 and messages.dtosb is not null and messages.kvt2=1 then 'ДС'
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
order by ns,dtosb,ksb
;

--select distinct ns, count(*) as cnt from orion.tsb group by ns order by cnt desc,ns;

======================

select 
(case when kvt1 is null then 'X' else text(kvt1) end ) ||
(case when kvt2 is null then 'X' else text(kvt2) end ) as kvt, 
dtosb, kvt1, kvt2
from orion.tsb;

--------

--
--  Function returns routes temp table
--
CREATE OR REPLACE FUNCTION orion.routes_fn (
    p_ns integer,
    p_dts timestamp without time zone DEFAULT NULL
    )
    RETURNS SETOF orion.t_routes
    AS
$BODY$ 
    DECLARE
        rec RECORD;
        l_ns integer;
        l_ksb bigint;
        l_lgn character varying(40);
        l_ldata integer default 0;
        l_mtype varchar(20);
        l_codes char(2);
        l_coder char(2);
        l_code char(2);
        l_codea char(2);
        l_codeb char(2);
        l_sender varchar(20);
        l_receiver varchar(20);
        l_nd1 bigint;
        l_rd1 timestamp without time zone;
        l_sd1 timestamp without time zone;
        l_er1 smallint;
        l_nd0 bigint;
        l_rd0 timestamp without time zone;
        l_sd0 timestamp without time zone;
        l_er0 smallint;
        l_nd2 bigint;
        l_rd2 timestamp without time zone;
        l_sd2 timestamp without time zone;
        l_er2 smallint;
        l_res char(2);
    
    croutes CURSOR FOR 
        select ns, ksb, lgn, ldata, mtype.itsb as mtype, mtype.ktsb,
            messages.kuoo, text(ts.nsch) || text(ts.nkts) as codes,
            (select isch from orion.tsch where ts.nsch=tsch.nsch) || ':' || ts.kikts as sender,
            messages.kuopr,     text(tb.nsch) || text(tb.nkts) as codeb,
            (select isch from orion.tsch where tb.nsch=tsch.nsch) || ':' || tb.kikts as _before,
            messages.kuo,     text(tn.nsch) || text(tn.nkts) as code, 
            (select isch from orion.tsch where tn.nsch=tsch.nsch) || ':' || tn.kikts as node,
            messages.kuosl, text(ta.nsch) || text(ta.nkts) as codea, 
            (select isch from orion.tsch where ta.nsch=tsch.nsch) || ':' || ta.kikts as _after,
            messages.kuoo,     text(tr.nsch) || text(tr.nkts) as coder, 
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
        where ns=p_ns;

  BEGIN
        DROP TABLE IF EXISTS routes;
        CREATE TEMP TABLE routes OF orion.t_routes;
    
        FOR rec IN croutes
                LOOP
                l_ns = rec.ns;
                l_ksb = rec.ksb;
                l_lgn = rec.lgn;
                l_mtype= rec.mtype;
                l_ldata = l_ldata + rec.ldata;
                l_sender = rec.sender;
                INSERT INTO routes(ns, lgn, mtype, ldata, sender) VALUES(
                    l_ns,
                    l_lgn,
                    l_mtype,
                    l_ldata,
                    l_sender
                );
                END LOOP;
  RETURN QUERY
  SELECT * FROM routes ORDER BY ns;
  RETURN;
  END;
 
$BODY$
     LANGUAGE 'plpgsql' VOLATILE
     COST 100
     ROWS 1000;

--ALTER FUNCTION orion.routes_fn (integer, timestamp without time zone) OWNER TO postgres;
--select * from orion.routes_fn(100);


--------

CREATE TYPE orion.t_routes AS (
    ns integer,
    lgn character varying(40),
    mtype varchar(20),
    ldata integer,
    sender varchar(20),
    receiver varchar(20),
    nd1 bigint,
    rd1 timestamp without time zone,
    sd1 timestamp without time zone,
    er1 smallint,
    nd0 bigint,
    rd0 timestamp without time zone,
    sd0 timestamp without time zone,
    er0 smallint,
    nd2 bigint,
    rd2 timestamp without time zone,
    sd2 timestamp without time zone,
    er2 smallint,
    res char(2)
);

DROP TABLE IF EXISTS routes;
CREATE TEMP TABLE IF NOT EXISTS routes OF orion.t_routes;

-----------

DROP TABLE IF EXISTS routes;
CREATE TEMP TABLE IF NOT EXISTS routes (
    ns integer,
    lgn character varying(40),
    mtype varchar(20),
    ldata integer,
    sender varchar(20),
    receiver varchar(20),
    nd1 bigint,
    rd1 timestamp without time zone,
    sd1 timestamp without time zone,
    er1 smallint,
    nd0 bigint,
    rd0 timestamp without time zone,
    sd0 timestamp without time zone,
    er0 smallint,
    nd2 bigint,
    rd2 timestamp without time zone,
    sd2 timestamp without time zone,
    er2 smallint,
    res char(2)
);
--select * from routes;
select c.relname, n.nspname from pg_namespace n
  join pg_class   c on n.oid=c.relnamespace
where n.nspname like 'pg_temp%'
order by n.nspname; 

-------

select ns, ksb, mtype.itsb as mtype, mtype.ktsb,
messages.kuoo, text(ts.nsch) || text(ts.nkts) as codes,
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
inner join orion.ttsb as mtype on mtype.ktsb=messages.ktsb
left outer join orion.tuo as tn on tn.kuo=messages.kuo
left outer join orion.tuo as ts on ts.kuo=messages.kuoo
left outer join orion.tuo as tr on tr.kuo=messages.kuop
left outer join orion.tuo as tb on tb.kuo=messages.kuopr
left outer join orion.tuo as ta on ta.kuo=messages.kuosl
--where tn.nsch=1 and tn.nkts=0
where ns=100
order by ksb
;

-------

select ns, ksb, mtype.itsb as mtype, mtype.ktsb,
messages.kuoo, text(ts.nsch) || text(ts.nkts) as codes,
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
inner join orion.ttsb as mtype on mtype.ktsb=messages.ktsb
left outer join orion.tuo as tn on tn.kuo=messages.kuo
left outer join orion.tuo as ts on ts.kuo=messages.kuoo
left outer join orion.tuo as tr on tr.kuo=messages.kuop
left outer join orion.tuo as tb on tb.kuo=messages.kuopr
left outer join orion.tuo as ta on ta.kuo=messages.kuosl
--where tn.nsch=1 and tn.nkts=0
where ns=100
order by ksb
;

-------------

select ns, ksb, mtype.itsb as mtype, mtype.ktsb,
messages.kuoo, text(ts.nsch) || text(ts.nkts) as codes,
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
inner join orion.ttsb as mtype on mtype.ktsb=messages.ktsb
left outer join orion.tuo as tn on tn.kuo=messages.kuo
left outer join orion.tuo as ts on ts.kuo=messages.kuoo
left outer join orion.tuo as tr on tr.kuo=messages.kuop
left outer join orion.tuo as tb on tb.kuo=messages.kuopr
left outer join orion.tuo as ta on ta.kuo=messages.kuosl
--where tn.nsch=1 and tn.nkts=0
where ns=100
order by ksb
;

--select ns, count(*) from orion.tsb group by ns order by ns;
select * from orion.tuo order by kuo;
select * from orion.tvsd order by ksd;