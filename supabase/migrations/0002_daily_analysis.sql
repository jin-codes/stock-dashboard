-- Daily fundamental/technical analysis, written by the daily script/Claude Code run.
-- Writes go through the service role key only (RLS blocks anon/authenticated writes);
-- reads are public, matching holdings/watchlist/daily_snapshots.

create table if not exists daily_analysis (
  id         uuid primary key default gen_random_uuid(),
  ticker     text not null,
  date       date not null,
  price      numeric not null,
  change_pct numeric,
  signal     text not null check (signal in ('보유', '추가매수', '추격매수금지', '매도', '매수')),
  reasoning  text,
  updated_at timestamptz not null default now(),
  unique (ticker, date)
);

create index if not exists daily_analysis_ticker_date_idx
  on daily_analysis (ticker, date desc);

drop trigger if exists daily_analysis_set_updated_at on daily_analysis;
create trigger daily_analysis_set_updated_at
  before update on daily_analysis
  for each row
  execute function set_updated_at();

alter table daily_analysis enable row level security;

drop policy if exists "daily_analysis_select" on daily_analysis;
create policy "daily_analysis_select" on daily_analysis
  for select using (true);
