# stock-dashboard

A personal stock portfolio analysis tool. There's no separate web/API
server — Supabase is the backend, and Python scripts run directly by
Claude Code (plus GitHub Actions) perform the daily automated analysis.

## Structure

- `supabase/migrations/` — DB schema
  - `0001_init.sql`: `holdings`, `watchlist`, `daily_snapshots`
  - `0002_daily_analysis.sql`: `daily_analysis` (daily analysis results)
  - `0003_portfolio_analysis.sql`: `portfolio_analysis` (overall portfolio summary)
  - `0004_expand_signals.sql`: expanded to 9 signal types
  - `0005_trades.sql`: `trades` (sell history / realized P&L)
  - `0006_split_chase_signal.sql`: split the "don't chase" signal into
    separate holdings/watchlist versions
  - `0007_intraday_snapshots.sql`: `intraday_snapshots` (10-minute price
    history, used for the dashboard's intraday chart)
  - `0008_portfolio_top_pick.sql`: adds `top_pick`, `top_pick_reason` to
    `portfolio_analysis` (the day's top pick among watchlist tickers)
  - `0009_english_signals.sql`: translates the `signal` taxonomy from
    Korean literals to English ones (e.g. `hold`, `buy`, `sell`)
- `scripts/` — Python scripts
  - `fetch_prices.py` — fetches prices via yfinance, saves to
    `daily_snapshots` (daily) and `intraday_snapshots` (10-minute history)
  - `portfolio.py` — CLI for reading/writing holdings/watchlist/daily_analysis/trades
  - `save_analysis.py` — upserts `daily_analysis`
  - `save_portfolio_summary.py` — upserts `portfolio_analysis` (summary +
    watchlist top pick `top_pick`/`top_pick_reason`)
  - `build_kakao_summary.py` — reads the day's summary + top pick from
    `portfolio_analysis` and assembles a KakaoTalk message under 200
    characters (see "KakaoTalk notifications" below)
  - `build_kakao_template.py` — converts that message into the
    `template_object` JSON for the Kakao "send to me" API
  - `lib/db.py` — shared Supabase client using the service role key
- `DAILY_ANALYSIS.md` — the daily analysis workflow procedure (followed
  by Claude Code)
- `INVESTMENT_PROFILE.md` — analysis criteria such as risk tolerance and
  investment horizon (no need to re-enter every time). Contains personal
  investment preferences, so it's gitignored — only the template
  `INVESTMENT_PROFILE.md.example` is committed to the repo
- `.claude/commands/daily-analysis.md` — a slash command that runs the
  above workflow directly in an interactive session via `/daily-analysis`
- `.github/workflows/daily-analysis.yml` — runs automatically every day
  at 07:00 KST (analysis + optional KakaoTalk notification)
- `docs/index.html` — a read-only dashboard deployed via GitHub Pages.
  Shows holdings/watchlist status along with the day's watchlist top
  pick, the reason it was picked, and past history

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r scripts/requirements.txt
cp .env.local.example .env.local  # fill in SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY
cp INVESTMENT_PROFILE.md.example INVESTMENT_PROFILE.md  # fill in your own investment profile
```

`SUPABASE_SERVICE_ROLE_KEY` bypasses RLS. Never commit it
(`.env.local` is already in `.gitignore`).

## Usage

```bash
# Read/write portfolio data (also works via natural language in a Claude Code session)
python scripts/portfolio.py holdings list
python scripts/portfolio.py holdings add AAPL --quantity 10 --avg-cost 150 --first-buy-date 2024-01-01 --thesis "..."
python scripts/portfolio.py watchlist add NVDA --target-price 900 --thesis "..."
python scripts/portfolio.py holdings sell AAPL --quantity 4 --price 227.5 --note "partial profit-taking"
python scripts/portfolio.py trades list

# Just fetch prices
python scripts/fetch_prices.py

# Run the full daily analysis workflow (fetch prices + news research + signal
# judgment + save)
# In a Claude Code session: /daily-analysis
```

## GitHub Actions automation

`.github/workflows/daily-analysis.yml` runs the procedure in
`DAILY_ANALYSIS.md` headlessly via Claude Code every day at 22:00 UTC
(07:00 KST). You need to register the following repo secrets:

- `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`
- `CLAUDE_CODE_OAUTH_TOKEN` — issued locally via `claude setup-token`
  (billed against your subscription credits, no separate API charges)
- `INVESTMENT_PROFILE_MD` (optional) — since `INVESTMENT_PROFILE.md`
  contains personal investment preferences and isn't committed to the
  repo, register its contents as this secret if you want automated runs
  to take it into account:
  ```bash
  gh secret set INVESTMENT_PROFILE_MD < INVESTMENT_PROFILE.md
  ```
  If not set, the workflow analyzes using neutral criteria without this file.

The workflow runs with `--dangerously-skip-permissions` (headless CI can't
show approval prompts). Each run is isolated to a fresh runner and only
touches this repo's scripts, so the risk is low, but be careful when
editing the workflow file.

## KakaoTalk notifications (optional)

After each day's analysis finishes, it can send a portfolio summary +
watchlist top pick as a KakaoTalk "send to me" message under 200
characters. This is entirely optional — if you don't register the
secrets below, this step is silently skipped (`continue-on-error`) and
has no effect on the main `daily-analysis` job.

### 1. Create a Kakao app

1. [Kakao Developers](https://developers.kakao.com) → My Applications →
   Add Application
2. **App Settings → Platform** → register a Web platform (any site
   domain works, e.g. `https://localhost.com`)
3. **App Settings → App Keys** → note the REST API key
4. **Product Settings → Kakao Login** → turn Activation ON, register a
   Redirect URI (this must be registered separately here, even though
   you already registered a domain in the platform step, e.g.
   `https://localhost.com/oauth`)
5. **Product Settings → Kakao Login → Consent Items** → enable "Send
   KakaoTalk Messages" (`talk_message`)
6. **Product Settings → Kakao Login → Security** → if Client Secret is
   turned on, note its value (if it's off, skip the related secret below)

### 2. Issue a refresh_token (one-time, in a browser)

Open the URL below to log in and consent:

```
https://kauth.kakao.com/oauth/authorize?client_id=<REST_API_KEY>&redirect_uri=<Redirect_URI>&response_type=code&scope=talk_message
```

Copy the `code` value from the redirected address
(`<Redirect_URI>?code=...` — it's fine even if it shows an error page),
then exchange it for a token in your terminal:

```bash
curl -X POST "https://kauth.kakao.com/oauth/token" \
  -H "Content-Type: application/x-www-form-urlencoded;charset=utf-8" \
  --data-urlencode "grant_type=authorization_code" \
  --data-urlencode "client_id=<REST_API_KEY>" \
  --data-urlencode "client_secret=<Client_Secret, if any>" \
  --data-urlencode "redirect_uri=<Redirect_URI>" \
  --data-urlencode "code=<copied code>"
```

Register the `refresh_token` from the response as the GitHub secret below.

### 3. Register GitHub Secrets

- `KAKAO_REST_API_KEY`
- `KAKAO_CLIENT_SECRET` (if Client Secret is enabled)
- `KAKAO_REFRESH_TOKEN` (the value issued above)

### Notes

- The `refresh_token` expires roughly 60 days after issuance. When it
  expires, only the "Send Kakao daily summary" step fails (as a
  warning) while everything else keeps working normally — just redo
  step 2 to refresh `KAKAO_REFRESH_TOKEN`.
- The message body is assembled by `build_kakao_summary.py` from that
  day's `portfolio_analysis.summary` and `top_pick` (if any). Edit that
  script if you want to change the format.
