-- Expand the daily_analysis signal taxonomy from 5 to 9 values, mainly to
-- give a fundamental-warning signal its own category (was previously buried
-- in reasoning text under 보유), and to distinguish partial trims / urgent
-- exits from a regular 매도.
--
-- Drops whatever the existing check constraint on `signal` is named (the
-- original migration relied on Postgres's default naming, which isn't
-- guaranteed) and replaces it with the expanded list.

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
    '추가매수',     -- thesis 강화, 비중 확대
    '보유',         -- thesis 유효, 현상 유지
    '관찰필요',     -- thesis 대체로 유효하나 초기 경고 신호 있음, 주시 필요
    '비중축소',     -- 부분 익절/리스크 축소, 완전 청산은 아님
    '매도',         -- thesis 훼손, 포지션 청산
    '긴급매도',     -- 심각한 악재로 즉시 청산 권고 (매도보다 높은 긴급도)
    '매수',         -- 관심종목 신규 진입 근거 확인
    '추격매수금지', -- 단기 과열, 지금 진입/추가는 비추천
    '관심제외'      -- 관심종목에서 제외 권고 (thesis 무산 등)
  ));
