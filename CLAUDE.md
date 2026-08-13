# stock-dashboard

개인용 주식 포트폴리오 분석 저장소. 웹 프론트엔드/API 서버 없음 — Supabase +
Python 스크립트 + Claude Code(대화형 또는 GitHub Actions 헤드리스) 조합으로만
동작합니다.

- 스키마 변경은 `supabase/migrations/`에 새 SQL 파일을 추가하는 방식으로만
  (기존 마이그레이션은 수정하지 말 것)
- `scripts/`는 Python. DB 접근은 `scripts/lib/db.py`의 `get_client()`
  (service role key, RLS 우회)를 통해서만
- 포트폴리오 조회/수정 요청은 `scripts/portfolio.py` CLI로 처리
- 매일 분석 절차는 `DAILY_ANALYSIS.md` 참고, 대화형 세션에서는
  `/daily-analysis`로 실행 가능
- 종목 신호 판단 시 `INVESTMENT_PROFILE.md`(리스크 성향/투자 기간/집중도
  기준)가 있으면 항상 반영할 것 — 사용자에게 매번 다시 물어보지 말 것.
  이 파일은 개인 투자 성향이 담겨 있어 `.gitignore`에 포함되며 저장소에는
  `INVESTMENT_PROFILE.md.example`만 커밋됨 — 새로 세팅하는 사용자는 이
  예시를 복사해서 본인 성향에 맞게 채울 것
- `.env.local`은 절대 커밋하지 말 것 (service role key 포함)
