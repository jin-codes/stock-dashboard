#!/usr/bin/env python3
"""Upsert one row into daily_analysis. Called at the end of the daily workflow
once Claude Code has reasoned about a ticker's signal from price + news + thesis.

Example:
  python scripts/save_analysis.py AAPL --date 2026-08-13 --price 227.5 \\
      --change-pct 1.2 --signal 보유 --reasoning "실적 예상치 상회, thesis 유효"
"""
import argparse
import json

from lib.db import get_client

SIGNALS = [
    "추가매수",
    "보유",
    "관찰필요",
    "비중축소",
    "매도",
    "긴급매도",
    "매수",
    "매수보류",
    "추격매수금지",
    "관심제외",
]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("ticker")
    parser.add_argument("--date", required=True, help="YYYY-MM-DD")
    parser.add_argument("--price", type=float, required=True)
    parser.add_argument("--change-pct", type=float)
    parser.add_argument("--signal", required=True, choices=SIGNALS)
    parser.add_argument("--reasoning", required=True)
    args = parser.parse_args()

    row = {
        "ticker": args.ticker.upper(),
        "date": args.date,
        "price": args.price,
        "change_pct": args.change_pct,
        "signal": args.signal,
        "reasoning": args.reasoning,
    }

    client = get_client()
    result = client.table("daily_analysis").upsert(row, on_conflict="ticker,date").execute()
    print(json.dumps(result.data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
