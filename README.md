# stock-dashboard

개인용 주식 포트폴리오 분석 도구. 별도 웹서버/API 서버 없이, Supabase를
백엔드로 두고 Claude Code가 직접 실행하는 Python 스크립트 + GitHub Actions로
매일 자동 분석합니다.

## 구성

- `supabase/migrations/` — DB 스키마
  - `0001_init.sql`: `holdings`, `watchlist`, `daily_snapshots`
  - `0002_daily_analysis.sql`: `daily_analysis` (매일 분석 결과)
- `scripts/` — Python 스크립트
  - `fetch_prices.py` — yfinance로 시세 수집, `daily_snapshots`에 저장
  - `portfolio.py` — holdings/watchlist/daily_analysis 조회 및 CRUD CLI
  - `save_analysis.py` — `daily_analysis` upsert
  - `lib/db.py` — service role 키로 Supabase 연결하는 공용 클라이언트
- `DAILY_ANALYSIS.md` — 매일 분석 워크플로 절차 (Claude Code가 따라 실행)
- `.claude/commands/daily-analysis.md` — 위 워크플로를 `/daily-analysis`로
  대화형 세션에서 바로 실행할 수 있는 슬래시 커맨드
- `.github/workflows/daily-analysis.yml` — 매일 07:00 KST 자동 실행

## 로컬 설정

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r scripts/requirements.txt
cp .env.local.example .env.local  # SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY 채우기
```

`SUPABASE_SERVICE_ROLE_KEY`는 RLS를 우회하는 키입니다. 절대 커밋하지 마세요
(`.env.local`은 `.gitignore`에 포함되어 있습니다).

## 사용법

```bash
# 포트폴리오 조회/수정 (Claude Code 세션에서 자연어로 요청해도 동일하게 동작)
python scripts/portfolio.py holdings list
python scripts/portfolio.py holdings add AAPL --quantity 10 --avg-cost 150 --first-buy-date 2024-01-01 --thesis "..."
python scripts/portfolio.py watchlist add NVDA --target-price 900 --thesis "..."

# 시세만 수집
python scripts/fetch_prices.py

# 일일 분석 워크플로 전체 실행 (가격 수집 + 뉴스 리서치 + 신호 판단 + 저장)
# Claude Code 세션에서: /daily-analysis
```

## GitHub Actions 자동 실행

매일 22:00 UTC(07:00 KST)에 `.github/workflows/daily-analysis.yml`이
`DAILY_ANALYSIS.md`의 절차를 헤드리스 Claude Code로 실행합니다. Repo secrets에
아래 값을 등록해야 합니다:

- `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`
- `CLAUDE_CODE_OAUTH_TOKEN` — 로컬에서 `claude setup-token`으로 발급 (구독
  크레딧으로 처리되며 별도 API 과금 없음)

워크플로는 `--dangerously-skip-permissions`로 실행됩니다 (헤드리스 CI라 승인
프롬프트를 띄울 수 없음). 매 실행이 격리된 새 러너에서 이 저장소의 스크립트만
다루므로 리스크는 낮지만, 워크플로 파일을 수정할 땐 유의하세요.
