# stock-dashboard

개인용 주식 포트폴리오 분석 도구. 별도 웹서버/API 서버 없이, Supabase를
백엔드로 두고 Claude Code가 직접 실행하는 Python 스크립트 + GitHub Actions로
매일 자동 분석합니다.

## 구성

- `supabase/migrations/` — DB 스키마
  - `0001_init.sql`: `holdings`, `watchlist`, `daily_snapshots`
  - `0002_daily_analysis.sql`: `daily_analysis` (매일 분석 결과)
  - `0003_portfolio_analysis.sql`: `portfolio_analysis` (포트폴리오 전체 요약)
  - `0004_expand_signals.sql`: signal 9종으로 확장
  - `0005_trades.sql`: `trades` (매도 이력/실현손익)
  - `0006_split_chase_signal.sql`: 추격매수금지 신호를 보유/관심 종목용으로 분리
  - `0007_intraday_snapshots.sql`: `intraday_snapshots` (10분 단위 시세 이력,
    대시보드 당일 차트용)
- `scripts/` — Python 스크립트
  - `fetch_prices.py` — yfinance로 시세 수집, `daily_snapshots`(일별)와
    `intraday_snapshots`(10분 단위 이력)에 저장
  - `portfolio.py` — holdings/watchlist/daily_analysis/trades 조회 및 CRUD CLI
  - `save_analysis.py` — `daily_analysis` upsert
  - `save_portfolio_summary.py` — `portfolio_analysis` upsert
  - `build_kakao_summary.py` — `portfolio_analysis` + `daily_analysis`에서
    당일 요약/신호를 읽어 200자 이내 카카오톡 메시지 텍스트로 조립 (아래
    "카카오톡 알림" 참고)
  - `build_kakao_template.py` — 위 메시지를 카카오 "나에게 보내기" API의
    `template_object` JSON으로 변환
  - `lib/db.py` — service role 키로 Supabase 연결하는 공용 클라이언트
- `DAILY_ANALYSIS.md` — 매일 분석 워크플로 절차 (Claude Code가 따라 실행)
- `INVESTMENT_PROFILE.md` — 리스크 성향/투자 기간 등 분석 기준 (매번 재입력
  불필요). 개인 투자 성향이 담겨 있어 `.gitignore` 처리됨 — 저장소에는
  템플릿인 `INVESTMENT_PROFILE.md.example`만 포함
- `.claude/commands/daily-analysis.md` — 위 워크플로를 `/daily-analysis`로
  대화형 세션에서 바로 실행할 수 있는 슬래시 커맨드
- `.github/workflows/daily-analysis.yml` — 매일 07:00 KST 자동 실행 (분석 +
  선택적으로 카카오톡 알림 발송)
- `docs/index.html` — GitHub Pages로 배포되는 읽기 전용 대시보드

## 로컬 설정

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r scripts/requirements.txt
cp .env.local.example .env.local  # SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY 채우기
cp INVESTMENT_PROFILE.md.example INVESTMENT_PROFILE.md  # 본인 투자 성향 채우기
```

`SUPABASE_SERVICE_ROLE_KEY`는 RLS를 우회하는 키입니다. 절대 커밋하지 마세요
(`.env.local`은 `.gitignore`에 포함되어 있습니다).

## 사용법

```bash
# 포트폴리오 조회/수정 (Claude Code 세션에서 자연어로 요청해도 동일하게 동작)
python scripts/portfolio.py holdings list
python scripts/portfolio.py holdings add AAPL --quantity 10 --avg-cost 150 --first-buy-date 2024-01-01 --thesis "..."
python scripts/portfolio.py watchlist add NVDA --target-price 900 --thesis "..."
python scripts/portfolio.py holdings sell AAPL --quantity 4 --price 227.5 --note "부분 익절"
python scripts/portfolio.py trades list

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
- `INVESTMENT_PROFILE_MD` (선택) — `INVESTMENT_PROFILE.md`는 개인 투자
  성향이 담겨 있어 저장소에 커밋되지 않으므로, 자동 실행에서도 반영하려면
  파일 내용을 그대로 이 secret에 등록하세요:
  ```bash
  gh secret set INVESTMENT_PROFILE_MD < INVESTMENT_PROFILE.md
  ```
  등록하지 않으면 워크플로는 이 파일 없이 중립적인 기준으로 분석합니다.

워크플로는 `--dangerously-skip-permissions`로 실행됩니다 (헤드리스 CI라 승인
프롬프트를 띄울 수 없음). 매 실행이 격리된 새 러너에서 이 저장소의 스크립트만
다루므로 리스크는 낮지만, 워크플로 파일을 수정할 땐 유의하세요.

## 카카오톡 알림 (선택)

매일 분석이 끝나면 카카오톡 "나에게 보내기"로 포트폴리오 요약 + 눈여겨볼
신호를 200자 이내 메시지로 보내줄 수 있습니다. 완전히 선택 사항이며, 아래
secrets를 등록하지 않으면 이 단계만 조용히 건너뜁니다(`continue-on-error`) —
`daily-analysis` 본 작업에는 영향 없습니다.

### 1. Kakao 앱 만들기

1. [Kakao Developers](https://developers.kakao.com) → 내 애플리케이션 →
   애플리케이션 추가하기
2. **앱 설정 → 플랫폼** → Web 플랫폼 등록 (사이트 도메인은 아무 값이나,
   예: `https://localhost.com`)
3. **앱 설정 → 앱 키** → REST API 키 확인
4. **제품 설정 → 카카오 로그인** → 활성화 ON, Redirect URI 등록 (플랫폼에
   등록한 도메인과 별개로 여기서도 등록해야 함, 예: `https://localhost.com/oauth`)
5. **제품 설정 → 카카오 로그인 → 동의항목** → "카카오톡 메시지 전송"
   (`talk_message`) 사용 설정
6. **제품 설정 → 카카오 로그인 → 보안** → Client Secret이 켜져 있다면 값 확인
   (꺼져 있다면 아래에서 관련 secret은 생략)

### 2. refresh_token 발급 (최초 1회, 브라우저에서)

아래 URL을 열어 로그인 + 동의:

```
https://kauth.kakao.com/oauth/authorize?client_id=<REST_API_키>&redirect_uri=<Redirect_URI>&response_type=code&scope=talk_message
```

리다이렉트된 주소(`<Redirect_URI>?code=...`, 에러 페이지가 떠도 정상)에서
`code` 값을 복사한 뒤, 터미널에서 토큰 교환:

```bash
curl -X POST "https://kauth.kakao.com/oauth/token" \
  -H "Content-Type: application/x-www-form-urlencoded;charset=utf-8" \
  --data-urlencode "grant_type=authorization_code" \
  --data-urlencode "client_id=<REST_API_키>" \
  --data-urlencode "client_secret=<Client_Secret, 있으면>" \
  --data-urlencode "redirect_uri=<Redirect_URI>" \
  --data-urlencode "code=<복사한 code>"
```

응답의 `refresh_token`을 아래 GitHub secret에 등록합니다.

### 3. GitHub Secrets 등록

- `KAKAO_REST_API_KEY`
- `KAKAO_CLIENT_SECRET` (Client Secret을 켰다면)
- `KAKAO_REFRESH_TOKEN` (위에서 발급받은 값)

### 참고

- `refresh_token`은 발급 후 약 60일 뒤 만료됩니다. 만료되면 "Send Kakao
  daily summary" 스텝만 실패(warning)하고 나머지는 정상 동작하니, 그때
  2번 과정을 다시 밟아 `KAKAO_REFRESH_TOKEN`을 갱신하세요.
- 메시지 본문은 `build_kakao_summary.py`가 그날 `portfolio_analysis.summary`
  와 `daily_analysis.signal`(보유 제외 신호만)을 조합해서 만듭니다. 형식을
  바꾸고 싶으면 이 스크립트를 수정하세요.
