-- "추격매수금지" was being used for both holdings ("don't add to this
-- position now") and watchlist ("don't enter now") cases, but the label
-- reads oddly for a name you don't hold yet. Split it: keep 추격매수금지
-- for holdings, add 매수보류 for watchlist "not an entry point yet".

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

alter table daily_analysis add constraint daily_analysis_signal_check
  check (signal in (
    '추가매수',     -- thesis 강화, 비중 확대 (holdings)
    '보유',         -- thesis 유효, 현상 유지 (holdings)
    '관찰필요',     -- thesis 대체로 유효하나 초기 경고 신호 있음, 주시 필요 (holdings)
    '비중축소',     -- 부분 익절/리스크 축소, 완전 청산은 아님 (holdings)
    '매도',         -- thesis 훼손, 포지션 청산 (holdings)
    '긴급매도',     -- 심각한 악재로 즉시 청산 권고 (holdings)
    '추격매수금지', -- 보유 포지션 단기 과열, 지금 추가 매수는 비추천 (holdings)
    '매수',         -- 관심종목 신규 진입 근거 확인 (watchlist)
    '매수보류',     -- 관심종목, thesis는 유효하나 지금은 진입 시점 아님 (watchlist)
    '관심제외'      -- 관심종목에서 제외 권고, thesis 무산 등 (watchlist)
  ));
