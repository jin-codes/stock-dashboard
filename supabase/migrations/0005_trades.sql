-- Realized P&L log. Written when a holding is (partially or fully) sold via
-- `scripts/portfolio.py holdings sell`. Kept separate from `holdings` since
-- a sell either shrinks or deletes the holdings row, and this history would
-- otherwise be lost. Same RLS pattern: public select, write via service role.

create table if not exists trades (
  id            uuid primary key default gen_random_uuid(),
  ticker        text not null,
  quantity      numeric not null check (quantity > 0),
  sell_price    numeric not null check (sell_price >= 0),
  cost_basis    numeric not null check (cost_basis >= 0), -- avg_cost per share at time of sale
  realized_pnl  numeric generated always as ((sell_price - cost_basis) * quantity) stored,
  sell_date     date not null,
  note          text,
  created_at    timestamptz not null default now()
);

create index if not exists trades_ticker_date_idx
  on trades (ticker, sell_date desc);

alter table trades enable row level security;

drop policy if exists "trades_select" on trades;
create policy "trades_select" on trades
  for select using (true);
