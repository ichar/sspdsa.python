--
-- Type for routes temp table
--
DROP TABLE IF EXISTS routes;
DROP TYPE IF EXISTS orion.t_routes;

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
