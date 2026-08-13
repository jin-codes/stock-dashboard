# 일일 포트폴리오 분석 워크플로

이 문서는 Claude Code가 (수동 실행이든 GitHub Actions 자동 실행이든) 매일
따라야 할 절차입니다. 결과는 `daily_analysis` 테이블에 저장됩니다.

## 절차

1. **가격 수집**
   ```
   python scripts/fetch_prices.py
   ```
   holdings + watchlist의 모든 티커에 대해 yfinance로 최신 종가/등락률/거래량을
   가져와 `daily_snapshots`에 저장하고, 결과를 JSON으로 출력합니다. 이 출력을
   이후 단계에서 가격/등락률 값으로 사용하세요.

2. **현재 포트폴리오 확인**
   ```
   python scripts/portfolio.py holdings list
   python scripts/portfolio.py watchlist list
   ```
   각 종목의 `thesis`(투자 근거)를 확인합니다.

3. **종목별 뉴스/실적 리서치**
   각 티커에 대해 WebSearch로 최근 1~2주 내 뉴스, 실적 발표, 가이던스 변경,
   애널리스트 의견 등을 확인하세요. 목표는 1단계에서 나온 thesis가 여전히
   유효한지, 아니면 무너뜨리는 새로운 사실이 있는지 판단하는 것입니다.

4. **신호 판단**
   가격 변동 + 뉴스/실적 + thesis 유효성을 종합해서 아래 5가지 중 하나를
   신호(signal)로 결정하세요:

   | signal | 의미 | 주로 해당 |
   |---|---|---|
   | 보유 | thesis 유효, 현상 유지 | holdings |
   | 추가매수 | thesis 강화, 비중 확대 근거 있음 | holdings |
   | 추격매수금지 | 단기 급등 등으로 지금은 진입/추가 시점 아님, 관망 | holdings/watchlist |
   | 매도 | thesis 훼손, 포지션 축소/청산 근거 있음 | holdings |
   | 매수 | 신규 진입 근거 있음 (목표가 도달, thesis 확인 등) | watchlist |

5. **저장**
   각 티커마다:
   ```
   python scripts/save_analysis.py <TICKER> --date <오늘 날짜 YYYY-MM-DD> \
     --price <1단계에서 나온 가격> --change-pct <등락률> \
     --signal <위 5가지 중 하나> --reasoning "<근거를 2~4문장으로, 구체적 사실 인용>"
   ```
   `reasoning`은 "왜 이 신호인지"를 다음 사람이 읽고 바로 이해할 수 있게
   구체적으로 쓰세요 (예: "3분기 매출 가이던스 상향 발표, thesis의 핵심인
   클라우드 매출 성장세 확인됨").

6. **요약**
   마지막에 오늘 처리한 전체 티커와 각각의 signal을 표로 간단히 정리해서
   출력하세요.

## 참고

- 스크립트는 `.env.local`의 `SUPABASE_URL` / `SUPABASE_SERVICE_ROLE_KEY`로
  Supabase에 연결합니다 (RLS 우회, service role 전용).
- `daily_analysis`는 `(ticker, date)` unique라 같은 날 재실행해도 upsert로
  덮어씁니다 — 재실행이 안전합니다.
