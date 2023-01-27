--
-- Type for routes_fn function's cursor returns t_route type
--
DROP FUNCTION IF EXISTS orion.route_fn;
DROP FUNCTION IF EXISTS orion.routes_fn;
DROP TYPE IF EXISTS orion.t_route;
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
    dtosb timestamp without time zone
);
