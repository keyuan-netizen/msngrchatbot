--
-- PostgreSQL database dump
--

\restrict 8K0Hm28iIdkxQ2AXcOSWzFbpcwf4dQdmxhucJY1csEiHSgvKBEm4zsMO73ZYIv9

-- Dumped from database version 17.6 (Homebrew)
-- Dumped by pg_dump version 17.6 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: sender_type; Type: TYPE; Schema: public; Owner: keyuan
--

CREATE TYPE public.sender_type AS ENUM (
    'user',
    'bot',
    'agent'
);


ALTER TYPE public.sender_type OWNER TO keyuan;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: conversations; Type: TABLE; Schema: public; Owner: keyuan
--

CREATE TABLE public.conversations (
    id integer NOT NULL,
    user_id integer NOT NULL,
    status character varying(32) DEFAULT 'open'::character varying NOT NULL,
    confidence double precision,
    last_message_preview character varying(500),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.conversations OWNER TO keyuan;

--
-- Name: conversations_id_seq; Type: SEQUENCE; Schema: public; Owner: keyuan
--

CREATE SEQUENCE public.conversations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.conversations_id_seq OWNER TO keyuan;

--
-- Name: conversations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: keyuan
--

ALTER SEQUENCE public.conversations_id_seq OWNED BY public.conversations.id;


--
-- Name: escalation_tickets; Type: TABLE; Schema: public; Owner: keyuan
--

CREATE TABLE public.escalation_tickets (
    id integer NOT NULL,
    conversation_id integer NOT NULL,
    reason character varying(255) NOT NULL,
    payload json,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.escalation_tickets OWNER TO keyuan;

--
-- Name: escalation_tickets_id_seq; Type: SEQUENCE; Schema: public; Owner: keyuan
--

CREATE SEQUENCE public.escalation_tickets_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.escalation_tickets_id_seq OWNER TO keyuan;

--
-- Name: escalation_tickets_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: keyuan
--

ALTER SEQUENCE public.escalation_tickets_id_seq OWNED BY public.escalation_tickets.id;


--
-- Name: message_logs; Type: TABLE; Schema: public; Owner: keyuan
--

CREATE TABLE public.message_logs (
    id integer NOT NULL,
    conversation_id integer NOT NULL,
    role character varying(16) NOT NULL,
    content text NOT NULL,
    metadata json,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.message_logs OWNER TO keyuan;

--
-- Name: message_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: keyuan
--

CREATE SEQUENCE public.message_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.message_logs_id_seq OWNER TO keyuan;

--
-- Name: message_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: keyuan
--

ALTER SEQUENCE public.message_logs_id_seq OWNED BY public.message_logs.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: keyuan
--

CREATE TABLE public.users (
    id integer NOT NULL,
    messenger_id character varying(128) NOT NULL,
    display_name character varying(255),
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.users OWNER TO keyuan;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: keyuan
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO keyuan;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: keyuan
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: conversations id; Type: DEFAULT; Schema: public; Owner: keyuan
--

ALTER TABLE ONLY public.conversations ALTER COLUMN id SET DEFAULT nextval('public.conversations_id_seq'::regclass);


--
-- Name: escalation_tickets id; Type: DEFAULT; Schema: public; Owner: keyuan
--

ALTER TABLE ONLY public.escalation_tickets ALTER COLUMN id SET DEFAULT nextval('public.escalation_tickets_id_seq'::regclass);


--
-- Name: message_logs id; Type: DEFAULT; Schema: public; Owner: keyuan
--

ALTER TABLE ONLY public.message_logs ALTER COLUMN id SET DEFAULT nextval('public.message_logs_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: keyuan
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: conversations; Type: TABLE DATA; Schema: public; Owner: keyuan
--

COPY public.conversations (id, user_id, status, confidence, last_message_preview, created_at, updated_at) FROM stdin;
1	1	open	0.4	Hello, what are your hours?	2025-11-17 21:44:46.202896-08	2025-11-17 21:44:46.202896-08
2	2	open	0.85	What are your hours?	2025-11-17 21:54:21.584134-08	2025-11-17 21:54:21.584134-08
\.


--
-- Data for Name: escalation_tickets; Type: TABLE DATA; Schema: public; Owner: keyuan
--

COPY public.escalation_tickets (id, conversation_id, reason, payload, created_at) FROM stdin;
\.


--
-- Data for Name: message_logs; Type: TABLE DATA; Schema: public; Owner: keyuan
--

COPY public.message_logs (id, conversation_id, role, content, metadata, created_at) FROM stdin;
1	1	user	Hello, what are your hours?	{}	2025-11-17 21:44:46.202896-08
2	1	assistant	Ask me a question.	{"citations": []}	2025-11-17 21:44:46.202896-08
3	2	user	What are your hours?	{}	2025-11-17 21:54:21.584134-08
4	2	assistant	Hi! Could you please tell me which location or service you're asking about? I'd be happy to help with the hours once I have that info! 😊	{"citations": []}	2025-11-17 21:54:21.584134-08
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: keyuan
--

COPY public.users (id, messenger_id, display_name, created_at) FROM stdin;
1	TEST_USER_1	\N	2025-11-17 21:44:46.202896-08
2	USER_1	\N	2025-11-17 21:54:21.584134-08
\.


--
-- Name: conversations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: keyuan
--

SELECT pg_catalog.setval('public.conversations_id_seq', 2, true);


--
-- Name: escalation_tickets_id_seq; Type: SEQUENCE SET; Schema: public; Owner: keyuan
--

SELECT pg_catalog.setval('public.escalation_tickets_id_seq', 1, false);


--
-- Name: message_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: keyuan
--

SELECT pg_catalog.setval('public.message_logs_id_seq', 4, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: keyuan
--

SELECT pg_catalog.setval('public.users_id_seq', 2, true);


--
-- Name: conversations conversations_pkey; Type: CONSTRAINT; Schema: public; Owner: keyuan
--

ALTER TABLE ONLY public.conversations
    ADD CONSTRAINT conversations_pkey PRIMARY KEY (id);


--
-- Name: escalation_tickets escalation_tickets_pkey; Type: CONSTRAINT; Schema: public; Owner: keyuan
--

ALTER TABLE ONLY public.escalation_tickets
    ADD CONSTRAINT escalation_tickets_pkey PRIMARY KEY (id);


--
-- Name: message_logs message_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: keyuan
--

ALTER TABLE ONLY public.message_logs
    ADD CONSTRAINT message_logs_pkey PRIMARY KEY (id);


--
-- Name: users users_messenger_id_key; Type: CONSTRAINT; Schema: public; Owner: keyuan
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_messenger_id_key UNIQUE (messenger_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: keyuan
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: conversations conversations_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: keyuan
--

ALTER TABLE ONLY public.conversations
    ADD CONSTRAINT conversations_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: escalation_tickets escalation_tickets_conversation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: keyuan
--

ALTER TABLE ONLY public.escalation_tickets
    ADD CONSTRAINT escalation_tickets_conversation_id_fkey FOREIGN KEY (conversation_id) REFERENCES public.conversations(id) ON DELETE CASCADE;


--
-- Name: message_logs message_logs_conversation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: keyuan
--

ALTER TABLE ONLY public.message_logs
    ADD CONSTRAINT message_logs_conversation_id_fkey FOREIGN KEY (conversation_id) REFERENCES public.conversations(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict 8K0Hm28iIdkxQ2AXcOSWzFbpcwf4dQdmxhucJY1csEiHSgvKBEm4zsMO73ZYIv9

