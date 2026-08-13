-- Portfolio-level daily summary (as opposed to daily_analysis, which is
-- per-ticker). One row per day. Same RLS pattern: public select, write via
-- service role only.

create table if not exists portfolio_analysis (
  id         uuid primary key default gen_random_uuid(),
  date       date not null unique,
  summary    text not null,
  updated_at timestamptz not null default now()
);

drop trigger if exists portfolio_analysis_set_updated_at on portfolio_analysis;
create trigger portfolio_analysis_set_updated_at
  before update on portfolio_analysis
  for each row
  execute function set_updated_at();

alter table portfolio_analysis enable row level security;

drop policy if exists "portfolio_analysis_select" on portfolio_analysis;
create policy "portfolio_analysis_select" on portfolio_analysis
  for select using (true);
