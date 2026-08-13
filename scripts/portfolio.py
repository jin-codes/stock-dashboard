#!/usr/bin/env python3
"""CLI for reading and editing holdings/watchlist/daily_analysis.
Meant to be invoked directly by a Claude Code session from natural language
requests, e.g. "AAPL 10주 평단 150에 추가해줘" -> holdings add.

Examples:
  python scripts/portfolio.py holdings list
  python scripts/portfolio.py holdings add AAPL --quantity 10 --avg-cost 150 --first-buy-date 2024-01-01 --thesis "..."
  python scripts/portfolio.py holdings update AAPL --quantity 12
  python scripts/portfolio.py holdings delete AAPL
  python scripts/portfolio.py holdings sell AAPL --quantity 4 --price 227.5 [--date 2026-08-13] [--note "..."]

  python scripts/portfolio.py watchlist list
  python scripts/portfolio.py watchlist add NVDA --target-price 900 --thesis "..."
  python scripts/portfolio.py watchlist update NVDA --target-price 950
  python scripts/portfolio.py watchlist delete NVDA

  python scripts/portfolio.py analysis list [--ticker AAPL] [--date 2026-08-13] [--limit 20]

  python scripts/portfolio.py trades list [--ticker AAPL] [--limit 20]

  python scripts/portfolio.py report summary
  python scripts/portfolio.py report watchlist
"""
import argparse
import datetime
import json
import sys

from lib.db import get_client

EPSILON = 1e-9


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


def cmd_holdings_sell(client, args):
    ticker = args.ticker.upper()
    holding = (
        client.table("holdings").select("*").eq("ticker", ticker).limit(1).execute().data
    )
    if not holding:
        print(f"{ticker}는 보유 종목이 아닙니다", file=sys.stderr)
        sys.exit(1)
    holding = holding[0]

    if args.quantity > holding["quantity"] + EPSILON:
        print(
            f"매도 수량({args.quantity})이 보유 수량({holding['quantity']})보다 많습니다",
            file=sys.stderr,
        )
        sys.exit(1)

    sell_date = args.date or datetime.date.today().isoformat()
    trade_row = {
        "ticker": ticker,
        "quantity": args.quantity,
        "sell_price": args.price,
        "cost_basis": holding["avg_cost"],
        "sell_date": sell_date,
    }
    if args.note is not None:
        trade_row["note"] = args.note

    trade_result = client.table("trades").insert(trade_row).execute()

    remaining = holding["quantity"] - args.quantity
    if remaining <= EPSILON:
        holding_result = client.table("holdings").delete().eq("ticker", ticker).execute()
        status = "전량 매도, holdings에서 제거됨"
    else:
        holding_result = (
            client.table("holdings")
            .update({"quantity": remaining})
            .eq("ticker", ticker)
            .execute()
        )
        status = f"부분 매도, 잔여 수량 {remaining}"

    print(json.dumps({"trade": trade_result.data, "status": status}, indent=2, ensure_ascii=False, default=str))


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


def _latest_prices(client, tickers):
    prices = {}
    for ticker in tickers:
        rows = (
            client.table("daily_snapshots")
            .select("price,date")
            .eq("ticker", ticker)
            .order("date", desc=True)
            .limit(1)
            .execute()
            .data
        )
        if rows:
            prices[ticker] = rows[0]["price"]
    return prices


def cmd_report_summary(client, args):
    holdings = client.table("holdings").select("*").order("ticker").execute().data
    if not holdings:
        print("보유 종목이 없습니다", file=sys.stderr)
        return
    prices = _latest_prices(client, [h["ticker"] for h in holdings])

    rows = []
    total_cost = 0.0
    total_value = 0.0
    for h in holdings:
        ticker = h["ticker"]
        qty = h["quantity"]
        cost_basis = qty * h["avg_cost"]
        price = prices.get(ticker)
        row = {
            "ticker": ticker,
            "quantity": qty,
            "avg_cost": h["avg_cost"],
            "cost_basis": round(cost_basis, 2),
            "price": price,
        }
        if price is not None:
            market_value = qty * price
            unrealized_pnl = market_value - cost_basis
            row["market_value"] = round(market_value, 2)
            row["unrealized_pnl"] = round(unrealized_pnl, 2)
            row["unrealized_pnl_pct"] = round(unrealized_pnl / cost_basis * 100, 2) if cost_basis else None
            total_value += market_value
        else:
            row["note"] = "daily_snapshots에 가격 없음 (fetch_prices.py 먼저 실행)"
            total_value += cost_basis
        total_cost += cost_basis
        rows.append(row)

    for row in rows:
        row["allocation_pct"] = round(row.get("market_value", row["cost_basis"]) / total_value * 100, 2) if total_value else None

    total_realized = sum(
        r["realized_pnl"] for r in client.table("trades").select("realized_pnl").execute().data
    )

    summary = {
        "holdings": rows,
        "total_cost_basis": round(total_cost, 2),
        "total_market_value": round(total_value, 2),
        "total_unrealized_pnl": round(total_value - total_cost, 2),
        "total_unrealized_pnl_pct": round((total_value - total_cost) / total_cost * 100, 2) if total_cost else None,
        "total_realized_pnl": round(total_realized, 2),
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False, default=str))


def cmd_report_watchlist(client, args):
    watchlist = client.table("watchlist").select("*").order("ticker").execute().data
    if not watchlist:
        print("관심 종목이 없습니다", file=sys.stderr)
        return
    prices = _latest_prices(client, [w["ticker"] for w in watchlist])

    rows = []
    for w in watchlist:
        ticker = w["ticker"]
        price = prices.get(ticker)
        row = {
            "ticker": ticker,
            "price": price,
            "target_price": w.get("target_price"),
        }
        if price is not None and w.get("target_price"):
            row["distance_to_target_pct"] = round((w["target_price"] - price) / price * 100, 2)
        rows.append(row)
    print_rows(rows)


def cmd_trades_list(client, args):
    query = client.table("trades").select("*")
    if args.ticker:
        query = query.eq("ticker", args.ticker.upper())
    query = query.order("sell_date", desc=True).limit(args.limit)
    rows = query.execute().data
    total_realized = sum(r["realized_pnl"] for r in rows)
    print_rows(rows)
    print(f"\n총 실현손익 (표시된 {len(rows)}건 기준): {total_realized:+.2f}", file=sys.stderr)


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

    p = holdings_sub.add_parser("sell")
    p.add_argument("ticker")
    p.add_argument("--quantity", type=float, required=True)
    p.add_argument("--price", type=float, required=True)
    p.add_argument("--date", help="YYYY-MM-DD, 기본값 오늘")
    p.add_argument("--note")
    p.set_defaults(func=cmd_holdings_sell)

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

    trades = sub.add_parser("trades")
    trades_sub = trades.add_subparsers(dest="action", required=True)
    p = trades_sub.add_parser("list")
    p.add_argument("--ticker")
    p.add_argument("--limit", type=int, default=20)
    p.set_defaults(func=cmd_trades_list)

    report = sub.add_parser("report")
    report_sub = report.add_subparsers(dest="action", required=True)
    report_sub.add_parser("summary").set_defaults(func=cmd_report_summary)
    report_sub.add_parser("watchlist").set_defaults(func=cmd_report_watchlist)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    client = get_client()
    args.func(client, args)


if __name__ == "__main__":
    main()
