--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

--
-- Name: pguser; Type: DATABASE; Schema: -; Owner: pguser
--

CREATE DATABASE pguser WITH TEMPLATE = template0 ENCODING = 'UTF8' LC_COLLATE = 'C' LC_CTYPE = 'C';


ALTER DATABASE pguser OWNER TO pguser;

\connect pguser

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

--
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


SET search_path = public, pg_catalog;

--
-- Name: bar(character varying); Type: FUNCTION; Schema: public; Owner: pguser
--

CREATE FUNCTION bar(character varying) RETURNS boolean
    LANGUAGE plpgsql
    AS $_$
BEGIN
return ($1 like '%HIT from Haifa%') or ($1 like '%Hit from Haifa%');
END
$_$;


ALTER FUNCTION public.bar(character varying) OWNER TO pguser;

--
-- Name: blocked(timestamp without time zone); Type: FUNCTION; Schema: public; Owner: pguser
--

CREATE FUNCTION blocked(timestamp without time zone) RETURNS TABLE(s integer, t timestamp without time zone, h character varying, c bigint)
    LANGUAGE plpgsql
    AS $_$
BEGIN
return query select status, max(at_time) t, host, count(*) from reply where status >= 400 and at_time > $1 group by status, host order by t;
END
$_$;


ALTER FUNCTION public.blocked(timestamp without time zone) OWNER TO pguser;

--
-- Name: es_ip(character varying); Type: FUNCTION; Schema: public; Owner: pguser
--

CREATE FUNCTION es_ip(character varying) RETURNS boolean
    LANGUAGE plpgsql
    AS $_$
BEGIN
return ($1 similar to '\d+.\d+.\d+.\d+');
END
$_$;


ALTER FUNCTION public.es_ip(character varying) OWNER TO pguser;

--
-- Name: foo(integer); Type: FUNCTION; Schema: public; Owner: pguser
--

CREATE FUNCTION foo(integer) RETURNS integer
    LANGUAGE plpgsql
    AS $$
BEGIN
return 0;
END
$$;


ALTER FUNCTION public.foo(integer) OWNER TO pguser;

--
-- Name: id(character varying[]); Type: FUNCTION; Schema: public; Owner: pguser
--

CREATE FUNCTION id(character varying[]) RETURNS character varying[]
    LANGUAGE plpgsql
    AS $_$
BEGIN
return $1;
END
$_$;


ALTER FUNCTION public.id(character varying[]) OWNER TO pguser;

--
-- Name: is_bookmarkable(character varying); Type: FUNCTION; Schema: public; Owner: pguser
--

CREATE FUNCTION is_bookmarkable(character varying) RETURNS boolean
    LANGUAGE plpgsql
    AS $_$
BEGIN
return ($1 not like '%.jpg' and $1 not like '%.png' and $1 not like '%.gif' and $1 not like '%.css' and $1 not like '%.js' and $1 not like '%.ico' and $1 not like '%.jpeg' and $1 not like '%.ttf' and $1 not like '%.JPG' and $1 not like '%.svg' and $1 not like '%.json');
END
$_$;


ALTER FUNCTION public.is_bookmarkable(character varying) OWNER TO pguser;

--
-- Name: last(character varying[]); Type: FUNCTION; Schema: public; Owner: pguser
--

CREATE FUNCTION last(character varying[]) RETURNS character varying
    LANGUAGE plpgsql
    AS $_$
BEGIN
return ($1)[array_upper($1,1)];
END
$_$;


ALTER FUNCTION public.last(character varying[]) OWNER TO pguser;

--
-- Name: latest(timestamp without time zone); Type: FUNCTION; Schema: public; Owner: pguser
--

CREATE FUNCTION latest(timestamp without time zone) RETURNS TABLE(t timestamp without time zone, h character varying, c bigint)
    LANGUAGE plpgsql
    AS $_$
BEGIN
return query select max(at_time) t, host, count(*) from reply where status = 200 and at_time > $1 group by host order by t;
END
$_$;


ALTER FUNCTION public.latest(timestamp without time zone) OWNER TO pguser;

--
-- Name: longpath(character varying); Type: FUNCTION; Schema: public; Owner: pguser
--

CREATE FUNCTION longpath(character varying) RETURNS boolean
    LANGUAGE plpgsql
    AS $_$
BEGIN
return (array_length(regexp_split_to_array($1, '/'), 1) > 3);
END
$_$;


ALTER FUNCTION public.longpath(character varying) OWNER TO pguser;

--
-- Name: no_tld(character varying); Type: FUNCTION; Schema: public; Owner: pguser
--

CREATE FUNCTION no_tld(character varying) RETURNS character varying
    LANGUAGE plpgsql
    AS $_$
BEGIN
return (select (array_agg(unnest))[array_upper(array_agg(unnest),1)] from unnest(regexp_split_to_array($1,'\.')) where unnest not in (select tld from tlds));
END
$_$;


ALTER FUNCTION public.no_tld(character varying) OWNER TO pguser;

--
-- Name: no_tld_arr(character varying); Type: FUNCTION; Schema: public; Owner: pguser
--

CREATE FUNCTION no_tld_arr(character varying) RETURNS character varying[]
    LANGUAGE plpgsql
    AS $_$
BEGIN
return (select array_agg(unnest) from unnest(regexp_split_to_array($1,'\.')) where unnest not in (select tld from tlds));
END
$_$;


ALTER FUNCTION public.no_tld_arr(character varying) OWNER TO pguser;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: banned; Type: TABLE; Schema: public; Owner: pguser; Tablespace: 
--

CREATE TABLE banned (
    url character varying(256)
);


ALTER TABLE public.banned OWNER TO pguser;

--
-- Name: filtro; Type: TABLE; Schema: public; Owner: pguser; Tablespace: 
--

CREATE TABLE filtro (
    host character varying(256)
);


ALTER TABLE public.filtro OWNER TO pguser;

--
-- Name: navigation; Type: TABLE; Schema: public; Owner: pguser; Tablespace: 
--

CREATE TABLE navigation (
    at_time timestamp without time zone,
    instance integer,
    scheme character varying(10),
    host character varying(256),
    path character varying(256),
    fragment character varying(256),
    query json
);


ALTER TABLE public.navigation OWNER TO pguser;

--
-- Name: reply; Type: TABLE; Schema: public; Owner: pguser; Tablespace: 
--

CREATE TABLE reply (
    at_time timestamp without time zone NOT NULL,
    instance integer NOT NULL,
    idx integer NOT NULL,
    status integer,
    scheme character varying(10),
    host character varying(256) NOT NULL,
    port integer,
    path character varying(2048) NOT NULL,
    fragment character varying(2048),
    query json,
    headers json
);


ALTER TABLE public.reply OWNER TO pguser;

--
-- Name: request; Type: TABLE; Schema: public; Owner: pguser; Tablespace: 
--

CREATE TABLE request (
    at_time timestamp without time zone NOT NULL,
    instance integer NOT NULL,
    idx integer NOT NULL,
    op character varying(10),
    scheme character varying(10),
    host character varying(256) NOT NULL,
    port integer,
    path character varying(2048) NOT NULL,
    fragment character varying(2048),
    query json,
    headers json,
    data json,
    source character varying(256)
);


ALTER TABLE public.request OWNER TO pguser;

--
-- Name: tlds; Type: TABLE; Schema: public; Owner: pguser; Tablespace: 
--

CREATE TABLE tlds (
    tld character varying(256)
);


ALTER TABLE public.tlds OWNER TO pguser;

--
-- Name: banned_url_key; Type: CONSTRAINT; Schema: public; Owner: pguser; Tablespace: 
--

ALTER TABLE ONLY banned
    ADD CONSTRAINT banned_url_key UNIQUE (url);


--
-- Name: filtro_host_key; Type: CONSTRAINT; Schema: public; Owner: pguser; Tablespace: 
--

ALTER TABLE ONLY filtro
    ADD CONSTRAINT filtro_host_key UNIQUE (host);


--
-- Name: tlds_tld_key; Type: CONSTRAINT; Schema: public; Owner: pguser; Tablespace: 
--

ALTER TABLE ONLY tlds
    ADD CONSTRAINT tlds_tld_key UNIQUE (tld);


--
-- Name: navigation_host_path_idx; Type: INDEX; Schema: public; Owner: pguser; Tablespace: 
--

CREATE INDEX navigation_host_path_idx ON navigation USING btree (host, path);


--
-- Name: public; Type: ACL; Schema: -; Owner: pgsql
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM pgsql;
GRANT ALL ON SCHEMA public TO pgsql;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- PostgreSQL database dump complete
--

