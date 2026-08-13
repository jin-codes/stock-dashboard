-- Personal stock dashboard schema
-- Read-only via anon key from the frontend; writes are done via service role
-- (Supabase MCP / scripts), so RLS only grants SELECT to anon/authenticated.

create extension if not exists "pgcrypto";

-- ---------------------------------------------------------------------------
-- holdings
-- ---------------------------------------------------------------------------
create table if not exists holdings (
  ticker         text primary key,
  quantity       numeric not null check (quantity >= 0),
  avg_cost       numeric not null check (avg_cost >= 0),
  first_buy_date date not null,
  thesis         text,
  updated_at     timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- watchlist
-- ---------------------------------------------------------------------------
create table if not exists watchlist (
  ticker       text primary key,
  target_price numeric,
  thesis       text,
  added_at     timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- daily_snapshots
-- ---------------------------------------------------------------------------
create table if not exists daily_snapshots (
  id         uuid primary key default gen_random_uuid(),
  ticker     text not null,
  date       date not null,
  price      numeric not null,
  change_pct numeric,
  volume     bigint,
  note       text,
  unique (ticker, date)
);

create index if not exists daily_snapshots_ticker_date_idx
  on daily_snapshots (ticker, date desc);

-- ---------------------------------------------------------------------------
-- updated_at trigger for holdings
-- ---------------------------------------------------------------------------
create or replace function set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

drop trigger if exists holdings_set_updated_at on holdings;
create trigger holdings_set_updated_at
  before update on holdings
  for each row
  execute function set_updated_at();

-- ---------------------------------------------------------------------------
-- Row Level Security: read-only for anon/authenticated clients.
-- Inserts/updates/deletes are expected to go through the service role key
-- (Supabase MCP or scripts), which bypasses RLS entirely.
-- ---------------------------------------------------------------------------
alter table holdings enable row level security;
alter table watchlist enable row level security;
alter table daily_snapshots enable row level security;

drop policy if exists "holdings_select" on holdings;
create policy "holdings_select" on holdings
  for select using (true);

drop policy if exists "watchlist_select" on watchlist;
create policy "watchlist_select" on watchlist
  for select using (true);

drop policy if exists "daily_snapshots_select" on daily_snapshots;
create policy "daily_snapshots_select" on daily_snapshots
  for select using (true);
