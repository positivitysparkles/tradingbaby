-- W118 "Curl if Flow" — Supabase schema
-- Run this in: supabase.com → tradingbaby project → SQL Editor → New query → Run
-- ─────────────────────────────────────────────────────────────────────────────

create table if not exists public.w118_trades (
  id           uuid primary key default gen_random_uuid(),
  created_at   timestamptz not null default now(),

  -- Trade identity
  date         date        not null,
  time_et      text        not null,
  ticker       text        not null,
  status       text        not null default 'open'
                           check (status in ('open', 'closed', 'stopped')),

  -- Prices & sizing
  entry_price  numeric(10,4),
  exit_price   numeric(10,4),
  qty          integer,
  stop_price   numeric(10,4),
  t1_price     numeric(10,4),
  t2_price     numeric(10,4),
  t3_price     numeric(10,4),

  -- P&L
  realized_pnl numeric(10,2),

  -- Setup quality (written at entry)
  setup_score  smallint default 0,
  setup_max    smallint default 5,
  deep_curl    boolean  default false,
  k_value      numeric(6,2),
  d_value      numeric(6,2),
  vol_ratio    numeric(6,2),
  macd_hist    numeric(10,6),
  macd_line    numeric(10,6),
  zlsma        numeric(10,4),

  -- Edge Engine (A+/A/B/C grade, catalyst tier, session bucket)
  grade        text,
  catalyst     text,
  session      text,

  -- Audit
  exit_reason  text,
  blockers     text,
  notes        text
);

-- If the table already existed before the Edge Engine, add the new columns:
alter table public.w118_trades add column if not exists grade    text;
alter table public.w118_trades add column if not exists catalyst text;
alter table public.w118_trades add column if not exists session  text;

-- Indexes
create index if not exists w118_trades_date_idx   on public.w118_trades (date desc);
create index if not exists w118_trades_ticker_idx on public.w118_trades (ticker);
create index if not exists w118_trades_status_idx on public.w118_trades (status);

-- RLS: anon key can only read; service_role key (bot) can write
alter table public.w118_trades enable row level security;

drop policy if exists "anon read" on public.w118_trades;
create policy "anon read"
  on public.w118_trades
  for select
  to anon
  using (true);

-- ── Edge memory — the bot's learned "what's working" snapshots ────────────────
create table if not exists public.w118_edge (
  id          uuid primary key default gen_random_uuid(),
  computed_at timestamptz not null default now(),
  n_closed    integer,
  phase       text,          -- 'learning' | 'tightening'
  summary     text,          -- one-line headline for Telegram + dashboard
  profile     jsonb          -- per-bucket win-rate / avg-pnl / count map
);

create index if not exists w118_edge_computed_idx on public.w118_edge (computed_at desc);

alter table public.w118_edge enable row level security;
drop policy if exists "anon read edge" on public.w118_edge;
create policy "anon read edge"
  on public.w118_edge
  for select
  to anon
  using (true);

-- Verify
select 'w118_trades + w118_edge ready' as status;
