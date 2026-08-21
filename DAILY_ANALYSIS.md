# Daily Portfolio Analysis Workflow

This document is the procedure Claude Code should follow every day
(whether run manually or headlessly via GitHub Actions). Results are
saved to the `daily_analysis`/`portfolio_analysis` tables.

**Before starting, if `INVESTMENT_PROFILE.md` exists, read it and carry
its risk tolerance / investment horizon / concentration stance directly
into your signal judgments and reasoning tone.** That file is the source
of truth — there's no need to ask the user again. It contains personal
investment preferences and is gitignored, so it isn't committed — if it
doesn't exist, tell the user to copy `INVESTMENT_PROFILE.md.example` and
fill it in, and until it's filled in, don't assume any particular
investment stance — judge signals on neutral criteria only.

**Always reference the previous day's analysis.** Don't re-derive every
signal from scratch each time — treat the most recent analysis
(reasoning, signal) as the baseline and ask "what has actually changed
since then?" If there's no new fact that would shake the thesis (a
guidance change, an earnings surprise, a meaningful shift in a key
metric, news, etc.), keep the previous signal and reasoning's conclusion
as-is — don't change the signal just because a day has passed, or to
vary the wording. Research and judge deeply enough that you can reliably
tell whether anything materially changed since yesterday. When you do
change a signal, state explicitly in the reasoning what changed relative
to the prior day that justified it.

**Every company has both good and bad points at the same time.** No
company is purely a positive or purely a negative story — keep this in
mind and don't let your research or reasoning conclude from only one
side. Especially when issuing a strong buy/sell signal (add more, sell,
urgent sell), confirm you've also weighed the opposing risk or positive
factor, and make sure the reasoning is balanced (e.g., "positive factor A
exists, but risk B also exists, and on balance X wins out").

## Procedure

1. **Fetch prices**
   ```
   python scripts/fetch_prices.py
   ```
   Fetches the latest close price / change % / volume via yfinance for
   every ticker in holdings + watchlist, saves it to `daily_snapshots`,
   and prints the result as JSON. Use this output as the price/change %
   values in later steps.

2. **Review the current portfolio**
   ```
   python scripts/portfolio.py holdings list
   python scripts/portfolio.py watchlist list
   ```
   Check each ticker's `thesis` (investment rationale).

3. **Review the previous day's analysis**
   ```
   python scripts/portfolio.py analysis list --ticker <TICKER> --limit 1
   ```
   Check each ticker's most recent signal/reasoning and use that
   conclusion as the baseline for today's analysis.

4. **Research news/earnings per ticker**
   For each ticker, use WebSearch to check news, earnings releases,
   guidance changes, and analyst opinions from the last 1–2 weeks. The
   goal is to determine whether the prior analysis's thesis/signal from
   step 3 still holds, or whether there's a new fact that undermines (or
   reinforces) it. If there's no new fact, that's your basis for keeping
   the prior signal.

5. **Decide the signal**
   Combine the price move + news/earnings + thesis validity + whether
   anything materially changed since the prior day's analysis to decide
   on exactly one of the 10 signals below. You must use the literal
   value shown — it's enforced by a DB check constraint:

   | signal (DB value) | meaning | mainly for |
   |---|---|---|
   | `add_more` | thesis reinforced, grounds to add to the position | holdings |
   | `hold` | thesis still holds, no change, nothing notable | holdings |
   | `watch` | thesis mostly holds but there's an early warning sign (demand softening, margin pressure starting, etc.) — not sell-worthy yet but needs watching | holdings |
   | `trim` | grounds for partial profit-taking / risk reduction, not a full exit (e.g. trimming part of a position that's run up too far) | holdings |
   | `sell` | thesis broken, grounds to exit the position | holdings |
   | `urgent_sell` | serious bad news (guidance withdrawn, accounting issue, loss of a key customer, etc.) warranting immediate exit — more urgent than `sell`, don't overuse | holdings |
   | `avoid_chasing` | an existing position has run up sharply short-term; now isn't the time to add more — wait and watch | holdings |
   | `buy` | grounds for a new entry (hit target price, thesis confirmed, etc.) | watchlist |
   | `buy_wait` | thesis still holds but a short-term spike/uncertainty means now isn't the entry point — wait and watch | watchlist |
   | `drop_watch` | thesis never held or has fallen apart — better to drop it from the watchlist | watchlist |

   `watch` is specifically the "fundamental warning" signal that
   `INVESTMENT_PROFILE.md` explicitly calls for — if there's a warning
   sign but it doesn't rise to a sell, don't flatten it into `hold`;
   use `watch`.

   **The signal value itself must always be the exact English literal
   above (enforced by the DB).** Everything you write in prose —
   `reasoning`, the portfolio `summary`, `top_pick_reason` — should be
   written in whatever language `INVESTMENT_PROFILE.md` specifies (see
   its "Analysis language" field). If that file doesn't exist or doesn't
   specify a language, default to English.

6. **Save**
   For each ticker:
   ```
   python scripts/save_analysis.py <TICKER> --date <today's date, YYYY-MM-DD> \
     --price <price from step 1> --change-pct <change %> \
     --signal <one of the 10 values above> --reasoning "<5-8 sentences citing concrete facts>"
   ```
   Write `reasoning` specifically enough that the next reader immediately
   understands "why this signal." Don't just list facts (price, news,
   earnings) — spell out how they hold up or break the thesis, and
   therefore why this signal follows (e.g. "Q3 revenue guidance raised,
   confirming the cloud-revenue-growth thesis"). If the signal is
   unchanged from the prior day, say "same as prior day — because ..."; if
   it changed, state what changed, so the next reader can immediately see
   whether anything moved.

7. **Portfolio-level analysis**
   Separately from individual ticker signals, look at the portfolio as a
   whole and summarize the following in 2–4 sentences:
   - The overall tone of the day (share of gainers/losers, main drivers)
   - If `INVESTMENT_PROFILE.md` names a concentrated theme/sector, call
     out explicitly whether there was any sign of fundamental damage
     across it (if not, say so explicitly — "no notable warnings")
   - What today's signal distribution suggests (e.g. lots of
     `avoid_chasing`/`buy_wait` might mean "short-term overheated" — interpret it)

8. **Pick the watchlist top pick**
   Gather every watchlist ticker whose signal today is `buy` and compare
   them.
   - If there are none, there's no top pick — save without
     `--top-pick`/`--top-pick-reason` in step 9.
   - If there's one or more, compare them on growth potential, structural
     competitive advantage, analyst consensus, relative strength versus
     today's market, etc., and pick the single ticker with the strongest
     case as the top pick. If `INVESTMENT_PROFILE.md` exists, weight its
     risk tolerance/concentration criteria first; otherwise judge on
     neutral fundamentals.
   - Even with multiple buy signals, don't mechanically re-rank every
     time — if yesterday's top pick still has the strongest case today,
     keep it. Only swap it out when another ticker has become clearly
     stronger, and state why in the reason if you do.

9. **Save**
   ```
   python scripts/save_portfolio_summary.py --date <today's date, YYYY-MM-DD> \
     --summary "<2-4 sentence summary>" \
     [--top-pick <TICKER> --top-pick-reason "<1-2 sentence reason>"]
   ```

10. **Summarize**
    Finally, print a short table + text summarizing every ticker handled
    today with its signal, the portfolio-level summary, and today's top
    pick (ticker + reason, if any).

## Notes

- The scripts connect to Supabase using `SUPABASE_URL` /
  `SUPABASE_SERVICE_ROLE_KEY` from `.env.local` (bypasses RLS,
  service-role only).
- `daily_analysis` is unique on `(ticker, date)` and `portfolio_analysis`
  is unique on `date`, so re-running on the same day safely overwrites
  via upsert — reruns are safe.
