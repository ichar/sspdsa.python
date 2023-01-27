--
-- Type for routes temp table
--
DROP TABLE IF EXISTS routes;
DROP TYPE IF EXISTS orion.t_routes CASCADE;

CREATE TYPE orion.t_routes AS (
    ns integer,
    lgn character varying(40),
    mtype varchar(20),
    ldata integer,
    sender varchar(20),
    receiver varchar(20),
    nd1 varchar(20),
    rd1 timestamp without time zone,
    sd1 timestamp without time zone,
    er1 char(2),
    nd2 varchar(20),
    rd2 timestamp without time zone,
    sd2 timestamp without time zone,
    er2 char(2),
    nd3 varchar(20),
    rd3 timestamp without time zone,
    sd3 timestamp without time zone,
    er3 char(2),
    res char(2)
);
--
-- Type for routes_fn function's cursor returns results data
--
--DROP FUNCTION IF EXISTS orion.route_fn;
--DROP FUNCTION IF EXISTS orion.routes_fn;
DROP TYPE IF EXISTS orion.t_route CASCADE;
CREATE TYPE orion.t_route AS (
    ns integer,
    ksb bigint,
    lgn character varying(40),
    ldata integer,
    mtype varchar(256),
    ktsb bigint,
    kuoo bigint,
    codes char(2),
    sender varchar(20),
    kuopr bigint,
    codeb char(2),
    _before varchar(20),
    kuo bigint,
    code char(2),
    node varchar(20),
    kuosl bigint,
    codea char(2),
    _after varchar(20),
    kuop bigint,
    coder char(2),
    receiver varchar(20),
    err char(2),
    kvt1 smallint,
    kvt2 smallint,
    dtosb timestamp without time zone,
    dtpsb timestamp without time zone
);
--
-- Type for routes note data item
--
DROP TYPE IF EXISTS orion.t_route_note CASCADE;
CREATE TYPE orion.t_route_note AS (
    is_done boolean,
    node_id bigint,
    code char(2),
    node_name varchar(20),
    rdt timestamp without time zone,
    sdt timestamp without time zone,
    err char(2)
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
    OUT rdt timestamp without time zone,
    OUT sdt timestamp without time zone,
    OUT err smallint
    ) AS $$
begin
    is_done = 0;
    node_id = null;
    code = '';
    node_name = '';
    rd = null;
    sd = null;
    err = '';
end
$$LANGUAGE 'plpgsql'
;
--
-- Function returns route record
--
CREATE OR REPLACE FUNCTION orion.route_fn (
    p_ns integer,
    p_dts timestamp without time zone DEFAULT NULL
    )
    RETURNS SETOF orion.t_route
    AS
$BODY$ 
  BEGIN
    RETURN QUERY
        select ns, ksb, lgn, ldata, mtype.itsb as mtype, mtype.ktsb,
            messages.kuoo, (text(ts.nsch) || text(ts.nkts))::char(2) as codes,
            ((select isch from orion.tsch where ts.nsch=tsch.nsch) || ':' || ts.kikts)::varchar(20) as sender,
            messages.kuopr, (text(tb.nsch) || text(tb.nkts))::char(2) as codeb,
            ((select isch from orion.tsch where tb.nsch=tsch.nsch) || ':' || tb.kikts)::varchar(20) as _before,
            messages.kuo,   (text(tn.nsch) || text(tn.nkts))::char(2) as code, 
            ((select isch from orion.tsch where tn.nsch=tsch.nsch) || ':' || tn.kikts)::varchar(20) as node,
            messages.kuosl, (text(ta.nsch) || text(ta.nkts))::char(2) as codea, 
            ((select isch from orion.tsch where ta.nsch=tsch.nsch) || ':' || ta.kikts)::varchar(20) as _after,
            messages.kuoo,  (text(tr.nsch) || text(tr.nkts))::char(2) as coder, 
            ((select isch from orion.tsch where tr.nsch=tsch.nsch) || ':' || tr.kikts)::varchar(20) as receiver,
        (case when messages.kvt1=0 and messages.kvt2 not in (0,1) then 'РС' 
             when messages.kvt1=1 and messages.dtosb is null and messages.kvt2 not in (0,1) then 'ИС'
             when messages.kvt1=1 and messages.dtosb is not null and messages.kvt2=0 then 'РС'
             when messages.kvt1=1 and messages.dtosb is not null and messages.kvt2=1 then 'ДС'
        else 'ИС' end):: char(2) as err,
        kvt1, kvt2, messages.dtosb, messages.dtpsb
        from orion.tsb as messages
        inner join orion.ttsb as mtype on mtype.ktsb=messages.ktsb
        left outer join orion.tuo as tn on tn.kuo=messages.kuo
        left outer join orion.tuo as ts on ts.kuo=messages.kuoo
        left outer join orion.tuo as tr on tr.kuo=messages.kuop
        left outer join orion.tuo as tb on tb.kuo=messages.kuopr
        left outer join orion.tuo as ta on ta.kuo=messages.kuosl
        --where tn.nsch=1 and tn.nkts=0
        where ns=p_ns;

    RETURN;
  END;
 
$BODY$
     LANGUAGE 'plpgsql' VOLATILE
     COST 100
     ROWS 1000;

--ALTER FUNCTION orion.route_fn (integer, timestamp without time zone) OWNER TO postgres;
--select * from orion.route_fn(100);

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
        l_lgn character varying(40);
        l_mtype varchar(20);
        l_ldata integer default 0;
        l_node1 orion.t_route_note;
        l_node2 orion.t_route_note;
        l_node3 orion.t_route_note;

    DECLARE
        l_kuoo bigint;
        l_sender varchar(20);
        l_receiver varchar(20);
        l_res char(2);
    
    croutes CURSOR FOR 
        select * from orion.route_fn(p_ns, p_dts) order by ns desc, ksb;

  BEGIN
    DROP TABLE IF EXISTS routes;
    CREATE TEMP TABLE routes OF orion.t_routes;
    
    l_ns = -1;
    
    FOR rec IN croutes
        LOOP
            l_ksb = rec.ksb;
            l_lgn = rec.lgn;
            l_mtype= rec.mtype;
            l_ldata = l_ldata + rec.ldata;
            l_sender = rec.sender
            l_receiver = rec.receiver

            if l_ns != rec.ns then 
                if l_ns > -1 then
                    INSERT INTO routes(
                        ns, lgn, mtype, ldata, 
                        sender, receiver,
                        nd1, rd1, sd1, er1,
                        nd2, rd2, sd2, er2,
                        nd3, rd3, sd3, er3,
                        res
                    ) VALUES(
                        l_ns,
                        l_lgn,
                        l_mtype,
                        l_ldata,
                        l_sender,
                        l_receiver,
                        l_node1.node_name,
                        l_node1.rd,
                        l_node1.sd,
                        l_node1.err,
                        l_node2.node_name,
                        l_node2.rd,
                        l_node2.sd,
                        l_node2.err,
                        l_node3.node_name,
                        l_node3.rd,
                        l_node3.sd,
                        l_node3.err,
                        l_res
                    );
                end if;
                select * into l_node1 from orion.clear_route_node_fn();
                select * into l_node2 from orion.clear_route_node_fn();
                select * into l_node3 from orion.clear_route_node_fn();
                l_ns = rec.ns;
            end if;
            if l_node1.is_done is not true then
                if l_node1.node_id is null then
                    l_node1.node_id = rec.kuosl;
                    l_kuoo = rec.kuoo;
                elsif l_node1.node_id == rec.kuo and l_kuoo == rec.kuoo then
                    l_node1.code = rec.codes;
                    l_node1.node_name = rec.sender;
                    l_node1.rd = rec.dtpsb;
                    l_node1.sd = rec.dtosb;
                    l_node1.err = rec.err;
                    l_node1.is_done = true
                end if
            elsif l_node2.is_done is not true then 
                if l_node2.node_id is null then
                    l_node2.node_id = rec.kuosl;
                    l_kuoo = rec.kuoo;
                elsif l_node2.node_id == rec.kuo and l_kuoo == rec.kuoo then
                    l_node2.code = rec.codes;
                    l_node2.node_name = rec.sender;
                    l_node2.rd = rec.dtpsb;
                    l_node2.sd = rec.dtosb;
                    l_node2.err = rec.err;
                    l_node2.is_done = true
                end if
            elsif l_node3.is_done is not true then
                if l_node3.node_id is null then
                    l_node3.node_id = rec.kuosl;
                    l_kuoo = rec.kuoo;
                elsif l_node3.node_id == rec.kuo and l_kuoo == rec.kuoo then
                    l_node3.code = rec.codes;
                    l_node3.node_name = rec.sender;
                    l_node3.rd = rec.dtpsb;
                    l_node3.sd = rec.dtosb;
                    l_node3.err = rec.err;
                    l_node3.is_done = true
                end if
            end if
            
            l_res = rec.err;
        END LOOP;
  
    RETURN QUERY SELECT * FROM routes ORDER BY ns;

    RETURN;
  END;
 
$BODY$
     LANGUAGE 'plpgsql' VOLATILE
     COST 100
     ROWS 1000;

--ALTER FUNCTION orion.routes_fn (integer, timestamp without time zone) OWNER TO postgres;
--select * from orion.routes_fn(100);
