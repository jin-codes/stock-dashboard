#!/usr/bin/env python3
"""Upsert the portfolio-level (as opposed to per-ticker) daily summary.

Example:
  python scripts/save_portfolio_summary.py --date 2026-08-13 --summary "..."
"""
import argparse
import json

from lib.db import get_client


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--date", required=True, help="YYYY-MM-DD")
    parser.add_argument("--summary", required=True)
    parser.add_argument("--top-pick", help="Today's top pick ticker among the watchlist (omit if there are no buy signals)")
    parser.add_argument("--top-pick-reason", help="Why this ticker was picked (1-2 sentences)")
    args = parser.parse_args()

    row = {"date": args.date, "summary": args.summary, "top_pick": args.top_pick, "top_pick_reason": args.top_pick_reason}

    client = get_client()
    result = (
        client.table("portfolio_analysis")
        .upsert(row, on_conflict="date")
        .execute()
    )
    print(json.dumps(result.data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
