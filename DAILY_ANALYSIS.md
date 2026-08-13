# 일일 포트폴리오 분석 워크플로

이 문서는 Claude Code가 (수동 실행이든 GitHub Actions 자동 실행이든) 매일
따라야 할 절차입니다. 결과는 `daily_analysis`/`portfolio_analysis` 테이블에
저장됩니다.

**시작 전에 `INVESTMENT_PROFILE.md`를 반드시 읽고, 거기 적힌 리스크 성향/투자
기간/집중도에 대한 태도를 신호 판단과 reasoning 톤에 그대로 반영하세요.**
사용자에게 다시 물어볼 필요 없이 그 파일이 기준입니다.

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
   가격 변동 + 뉴스/실적 + thesis 유효성을 종합해서 아래 10가지 중 하나를
   신호(signal)로 결정하세요. 반드시 이 값 그대로 사용 (DB check 제약):

   | signal | 의미 | 주로 해당 |
   |---|---|---|
   | 추가매수 | thesis 강화, 비중 확대 근거 있음 | holdings |
   | 보유 | thesis 유효, 현상 유지, 특이사항 없음 | holdings |
   | 관찰필요 | thesis 대체로 유효하나 초기 경고 신호 있음 (수요 둔화 조짐, 마진 압박 시작 등) — 아직 팔 정도는 아니지만 주시 필요 | holdings |
   | 비중축소 | 부분 익절/리스크 축소 근거 있음, 완전 청산은 아님 (예: 과도하게 오른 포지션의 일부 차익실현) | holdings |
   | 매도 | thesis 훼손, 포지션 청산 근거 있음 | holdings |
   | 긴급매도 | 심각한 악재(가이던스 철회, 회계 이슈, 핵심 고객 이탈 등)로 즉시 청산 권고 — 매도보다 긴급도 높음, 남발 금지 | holdings |
   | 추격매수금지 | 보유 포지션이 단기 급등 등으로 지금은 추가 매수 시점 아님, 관망 | holdings |
   | 매수 | 신규 진입 근거 있음 (목표가 도달, thesis 확인 등) | watchlist |
   | 매수보류 | thesis는 유효하나 단기 급등/불확실성 등으로 지금은 진입 시점 아님, 관망 | watchlist |
   | 관심제외 | thesis가 애초에 성립하지 않거나 무산됨, 관심종목에서 빼는 게 나음 | watchlist |

   `관찰필요`는 `INVESTMENT_PROFILE.md`가 명시적으로 요청한 "펀더멘털 경고"를
   위한 신호입니다 — 경고감이 있는데 매도까지는 아니라면 `보유`로 뭉개지 말고
   반드시 `관찰필요`를 쓰세요.

5. **저장**
   각 티커마다:
   ```
   python scripts/save_analysis.py <TICKER> --date <오늘 날짜 YYYY-MM-DD> \
     --price <1단계에서 나온 가격> --change-pct <등락률> \
     --signal <위 10가지 중 하나> --reasoning "<근거를 2~4문장으로, 구체적 사실 인용>"
   ```
   `reasoning`은 "왜 이 신호인지"를 다음 사람이 읽고 바로 이해할 수 있게
   구체적으로 쓰세요 (예: "3분기 매출 가이던스 상향 발표, thesis의 핵심인
   클라우드 매출 성장세 확인됨").

6. **포트폴리오 전체 분석**
   개별 종목 signal과 별개로, 포트폴리오 전체를 보고 아래를 2~4문장으로
   종합하세요:
   - 오늘 전체적으로 어떤 흐름이었는지 (상승/하락 종목 비중, 주요 동인)
   - `INVESTMENT_PROFILE.md`에서 요청한 대로, AI/반도체 테마 전반에 걸친
     펀더멘털 훼손 신호가 있었다면 명시적으로 경고 (없으면 "특이 경고 없음"
     이라고 명시)
   - 오늘 신호들의 분포(예: 추격매수금지/매수보류가 많으면 "단기 과열 구간" 등 해석)

   ```
   python scripts/save_portfolio_summary.py --date <오늘 날짜 YYYY-MM-DD> \
     --summary "<2~4문장 요약>"
   ```

7. **요약**
   마지막에 오늘 처리한 전체 티커와 각각의 signal, 그리고 포트폴리오 전체
   요약을 표+텍스트로 간단히 정리해서 출력하세요.

## 참고

- 스크립트는 `.env.local`의 `SUPABASE_URL` / `SUPABASE_SERVICE_ROLE_KEY`로
  Supabase에 연결합니다 (RLS 우회, service role 전용).
- `daily_analysis`는 `(ticker, date)` unique, `portfolio_analysis`는 `date`
  unique라 같은 날 재실행해도 upsert로 덮어씁니다 — 재실행이 안전합니다.
