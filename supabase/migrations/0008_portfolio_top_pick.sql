-- Add a daily "top pick" among watchlist buy-signal tickers to the
-- portfolio-level summary, so the daily analysis (and kakao notification)
-- can surface a single best idea instead of just a flat signal list.

alter table portfolio_analysis
  add column if not exists top_pick        text,
  add column if not exists top_pick_reason text;
