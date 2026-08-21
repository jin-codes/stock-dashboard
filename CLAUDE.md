# stock-dashboard

A personal stock portfolio analysis repository. There's no web frontend or
API server — it runs purely on the combination of Supabase + Python
scripts + Claude Code (interactive sessions, or headless via GitHub
Actions).

- Schema changes go in `supabase/migrations/` as new SQL files only (never
  edit an existing migration)
- `scripts/` is Python. Access the DB only through `get_client()` in
  `scripts/lib/db.py` (service role key, bypasses RLS)
- Handle portfolio read/write requests via the `scripts/portfolio.py` CLI
- See `DAILY_ANALYSIS.md` for the daily analysis procedure; in an
  interactive session it can be run with `/daily-analysis`
- If `INVESTMENT_PROFILE.md` (risk tolerance / investment horizon /
  concentration criteria) exists, always factor it into signal
  judgments — don't ask the user to restate it every time. It contains
  personal investment preferences, so it's gitignored; only
  `INVESTMENT_PROFILE.md.example` is committed to the repo — anyone
  setting this up fresh should copy that example and fill it in with
  their own profile
- Never commit `.env.local` (it contains the service role key)
