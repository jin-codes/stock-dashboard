#!/usr/bin/env python3
"""Build the portfolio summary message sent every morning via KakaoTalk
"Message to me".

Read by daily-analysis.yml (GitHub Actions, daily at 07:00 KST) after it
saves that day's analysis. If today's date has no data yet (Actions hasn't
finished, or failed), falls back to the most recent date available.

Truncates to a 200-char limit (a constraint of the KakaoTalk "message to
me" tool) and prints only the final string to stdout.

Usage:
  python scripts/build_kakao_summary.py [--date YYYY-MM-DD] [--max-len 200]
"""
import argparse
import datetime as dt

from lib.db import get_client

MAX_LEN_DEFAULT = 200


def fetch_portfolio_summary(client, date_str: str | None):
    q = client.table("portfolio_analysis").select("date,summary,top_pick").order("date", desc=True)
    if date_str:
        q = q.eq("date", date_str)
    rows = q.limit(1).execute().data
    if rows:
        return rows[0]
    if date_str:
        # No data for the requested date, fall back to the most recent one
        rows = (
            client.table("portfolio_analysis")
            .select("date,summary,top_pick")
            .order("date", desc=True)
            .limit(1)
            .execute()
            .data
        )
        return rows[0] if rows else None
    return None


def truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


def build_message(client, date_str: str | None, max_len: int) -> str:
    portfolio = fetch_portfolio_summary(client, date_str)
    if not portfolio:
        return "No portfolio analysis data yet. Check whether daily-analysis has run."

    actual_date = portfolio["date"]
    summary = portfolio["summary"] or ""
    top_pick = portfolio.get("top_pick") or ""

    date_label = dt.date.fromisoformat(actual_date).strftime("%m/%d")
    header = f"[Portfolio {date_label}] "
    tail = f" Top pick: {top_pick}" if top_pick else ""

    budget_for_summary = max_len - len(header) - len(tail)
    summary_part = truncate(summary, budget_for_summary) if budget_for_summary < len(summary) else summary
    message = f"{header}{summary_part}{tail}"
    return truncate(message, max_len)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", help="YYYY-MM-DD (default: today, KST)")
    parser.add_argument("--max-len", type=int, default=MAX_LEN_DEFAULT)
    args = parser.parse_args()

    date_str = args.date
    if not date_str:
        kst = dt.timezone(dt.timedelta(hours=9))
        date_str = dt.datetime.now(kst).date().isoformat()

    client = get_client()
    message = build_message(client, date_str, args.max_len)
    print(message)


if __name__ == "__main__":
    main()
