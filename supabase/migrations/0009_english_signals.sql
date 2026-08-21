-- Translate the daily_analysis.signal taxonomy from Korean literals to
-- English ones, so the schema/scripts read as an internationally usable
-- open-source project. Existing rows are remapped in place; the mapping is
-- 1:1 with the Korean values introduced in 0004/0006 (see those files for
-- the original meanings).

do $$
declare
  con record;
begin
  for con in
    select conname from pg_constraint
    where conrelid = 'daily_analysis'::regclass
      and contype = 'c'
      and pg_get_constraintdef(oid) ilike '%signal%'
  loop
    execute format('alter table daily_analysis drop constraint %I', con.conname);
  end loop;
end $$;

update daily_analysis set signal = case signal
  when '추가매수'     then 'add_more'
  when '보유'         then 'hold'
  when '관찰필요'     then 'watch'
  when '비중축소'     then 'trim'
  when '매도'         then 'sell'
  when '긴급매도'     then 'urgent_sell'
  when '추격매수금지' then 'avoid_chasing'
  when '매수'         then 'buy'
  when '매수보류'     then 'buy_wait'
  when '관심제외'     then 'drop_watch'
  else signal
end;

alter table daily_analysis add constraint daily_analysis_signal_check
  check (signal in (
    'add_more',      -- thesis reinforced, grounds to add to the position (holdings)
    'hold',          -- thesis still holds, no change (holdings)
    'watch',         -- thesis mostly holds but an early warning sign appeared (holdings)
    'trim',          -- partial profit-taking / risk reduction, not a full exit (holdings)
    'sell',          -- thesis broken, grounds to exit (holdings)
    'urgent_sell',   -- serious bad news, immediate exit recommended (holdings)
    'avoid_chasing', -- position ran up short-term, don't add more now (holdings)
    'buy',           -- grounds for a new entry (watchlist)
    'buy_wait',      -- thesis holds but not the entry point yet (watchlist)
    'drop_watch'     -- thesis never held or fell apart, drop from watchlist (watchlist)
  ));
