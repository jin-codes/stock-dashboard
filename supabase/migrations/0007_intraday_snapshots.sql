-- intraday_snapshots
-- ---------------------------------------------------------------------------
-- Keeps every 10-min price fetch (not just the last one per day) so the
-- dashboard chart can show intraday movement for the current trading day.
create table if not exists intraday_snapshots (
  id         uuid primary key default gen_random_uuid(),
  ticker     text not null,
  ts         timestamptz not null default now(),
  price      numeric not null,
  change_pct numeric,
  volume     bigint
);

create index if not exists intraday_snapshots_ticker_ts_idx
  on intraday_snapshots (ticker, ts desc);

alter table intraday_snapshots enable row level security;

drop policy if exists "intraday_snapshots_select" on intraday_snapshots;
create policy "intraday_snapshots_select" on intraday_snapshots
  for select using (true);
