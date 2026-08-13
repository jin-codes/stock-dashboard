#!/usr/bin/env python3
"""CLI for reading and editing holdings/watchlist/daily_analysis.
Meant to be invoked directly by a Claude Code session from natural language
requests, e.g. "AAPL 10주 평단 150에 추가해줘" -> holdings add.

Examples:
  python scripts/portfolio.py holdings list
  python scripts/portfolio.py holdings add AAPL --quantity 10 --avg-cost 150 --first-buy-date 2024-01-01 --thesis "..."
  python scripts/portfolio.py holdings update AAPL --quantity 12
  python scripts/portfolio.py holdings delete AAPL

  python scripts/portfolio.py watchlist list
  python scripts/portfolio.py watchlist add NVDA --target-price 900 --thesis "..."
  python scripts/portfolio.py watchlist update NVDA --target-price 950
  python scripts/portfolio.py watchlist delete NVDA

  python scripts/portfolio.py analysis list [--ticker AAPL] [--date 2026-08-13] [--limit 20]
"""
import argparse
import json
import sys

from lib.db import get_client


def print_rows(rows):
    print(json.dumps(rows, indent=2, ensure_ascii=False, default=str))


def cmd_holdings_list(client, args):
    print_rows(client.table("holdings").select("*").order("ticker").execute().data)


def cmd_holdings_add(client, args):
    row = {
        "ticker": args.ticker.upper(),
        "quantity": args.quantity,
        "avg_cost": args.avg_cost,
        "first_buy_date": args.first_buy_date,
    }
    if args.thesis is not None:
        row["thesis"] = args.thesis
    print_rows(client.table("holdings").insert(row).execute().data)


def cmd_holdings_update(client, args):
    updates = {}
    if args.quantity is not None:
        updates["quantity"] = args.quantity
    if args.avg_cost is not None:
        updates["avg_cost"] = args.avg_cost
    if args.first_buy_date is not None:
        updates["first_buy_date"] = args.first_buy_date
    if args.thesis is not None:
        updates["thesis"] = args.thesis
    if not updates:
        print("변경할 필드가 없습니다 (--quantity, --avg-cost, --first-buy-date, --thesis 중 하나 필요)", file=sys.stderr)
        sys.exit(1)
    print_rows(
        client.table("holdings").update(updates).eq("ticker", args.ticker.upper()).execute().data
    )


def cmd_holdings_delete(client, args):
    print_rows(client.table("holdings").delete().eq("ticker", args.ticker.upper()).execute().data)


def cmd_watchlist_list(client, args):
    print_rows(client.table("watchlist").select("*").order("ticker").execute().data)


def cmd_watchlist_add(client, args):
    row = {"ticker": args.ticker.upper()}
    if args.target_price is not None:
        row["target_price"] = args.target_price
    if args.thesis is not None:
        row["thesis"] = args.thesis
    print_rows(client.table("watchlist").insert(row).execute().data)


def cmd_watchlist_update(client, args):
    updates = {}
    if args.target_price is not None:
        updates["target_price"] = args.target_price
    if args.thesis is not None:
        updates["thesis"] = args.thesis
    if not updates:
        print("변경할 필드가 없습니다 (--target-price, --thesis 중 하나 필요)", file=sys.stderr)
        sys.exit(1)
    print_rows(
        client.table("watchlist").update(updates).eq("ticker", args.ticker.upper()).execute().data
    )


def cmd_watchlist_delete(client, args):
    print_rows(client.table("watchlist").delete().eq("ticker", args.ticker.upper()).execute().data)


def cmd_analysis_list(client, args):
    query = client.table("daily_analysis").select("*")
    if args.ticker:
        query = query.eq("ticker", args.ticker.upper())
    if args.date:
        query = query.eq("date", args.date)
    query = query.order("date", desc=True).limit(args.limit)
    print_rows(query.execute().data)


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="entity", required=True)

    holdings = sub.add_parser("holdings")
    holdings_sub = holdings.add_subparsers(dest="action", required=True)
    holdings_sub.add_parser("list").set_defaults(func=cmd_holdings_list)

    p = holdings_sub.add_parser("add")
    p.add_argument("ticker")
    p.add_argument("--quantity", type=float, required=True)
    p.add_argument("--avg-cost", type=float, required=True)
    p.add_argument("--first-buy-date", required=True, help="YYYY-MM-DD")
    p.add_argument("--thesis")
    p.set_defaults(func=cmd_holdings_add)

    p = holdings_sub.add_parser("update")
    p.add_argument("ticker")
    p.add_argument("--quantity", type=float)
    p.add_argument("--avg-cost", type=float)
    p.add_argument("--first-buy-date")
    p.add_argument("--thesis")
    p.set_defaults(func=cmd_holdings_update)

    p = holdings_sub.add_parser("delete")
    p.add_argument("ticker")
    p.set_defaults(func=cmd_holdings_delete)

    watchlist = sub.add_parser("watchlist")
    watchlist_sub = watchlist.add_subparsers(dest="action", required=True)
    watchlist_sub.add_parser("list").set_defaults(func=cmd_watchlist_list)

    p = watchlist_sub.add_parser("add")
    p.add_argument("ticker")
    p.add_argument("--target-price", type=float)
    p.add_argument("--thesis")
    p.set_defaults(func=cmd_watchlist_add)

    p = watchlist_sub.add_parser("update")
    p.add_argument("ticker")
    p.add_argument("--target-price", type=float)
    p.add_argument("--thesis")
    p.set_defaults(func=cmd_watchlist_update)

    p = watchlist_sub.add_parser("delete")
    p.add_argument("ticker")
    p.set_defaults(func=cmd_watchlist_delete)

    analysis = sub.add_parser("analysis")
    analysis_sub = analysis.add_subparsers(dest="action", required=True)
    p = analysis_sub.add_parser("list")
    p.add_argument("--ticker")
    p.add_argument("--date", help="YYYY-MM-DD")
    p.add_argument("--limit", type=int, default=20)
    p.set_defaults(func=cmd_analysis_list)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    client = get_client()
    args.func(client, args)


if __name__ == "__main__":
    main()
