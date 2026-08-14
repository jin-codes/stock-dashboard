#!/usr/bin/env python3
"""매일 아침 카카오톡 '나와의 채팅'으로 보낼 포트폴리오 요약 메시지를 만든다.

daily-analysis.yml (GitHub Actions, 매일 07:00 KST)가 그날 분석을 저장한 뒤
읽어가는 용도. 오늘 날짜 데이터가 아직 없으면 (Actions가 아직 안 끝났거나
실패한 경우) 가장 최근 날짜 데이터로 fallback 한다.

200자 제한(카카오톡 나와의 채팅 도구 제약)에 맞춰 자르고, 최종 문자열만
stdout에 출력한다.

Usage:
  python scripts/build_kakao_summary.py [--date YYYY-MM-DD] [--max-len 200]
"""
import argparse
import datetime as dt

from lib.db import get_client

MAX_LEN_DEFAULT = 200
NEUTRAL_SIGNAL = "보유"


def fetch_portfolio_summary(client, date_str: str | None):
    q = client.table("portfolio_analysis").select("date,summary").order("date", desc=True)
    if date_str:
        q = q.eq("date", date_str)
    rows = q.limit(1).execute().data
    if rows:
        return rows[0]
    if date_str:
        # 요청한 날짜 데이터가 없으면 가장 최근 날짜로 fallback
        rows = (
            client.table("portfolio_analysis")
            .select("date,summary")
            .order("date", desc=True)
            .limit(1)
            .execute()
            .data
        )
        return rows[0] if rows else None
    return None


def fetch_signals(client, date_str: str):
    rows = (
        client.table("daily_analysis")
        .select("ticker,signal")
        .eq("date", date_str)
        .order("ticker")
        .execute()
        .data
    )
    return rows or []


def truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


def build_notable_str(signals, max_items: int = 6) -> str:
    """눈여겨볼 종목(보유 신호 제외) 리스트를 최대 max_items개까지만 보여주고,
    나머지는 "외 N개"로 요약한다 - 종목이 많은 날 리스트만으로 200자를
    다 잡아먹고 요약 문장이 통째로 사라지는 걸 막기 위함."""
    notable = [(r["ticker"], r["signal"]) for r in signals if r["signal"] != NEUTRAL_SIGNAL]
    if not notable:
        return "특이 신호 없음"

    shown = notable[:max_items]
    notable_str = ", ".join(f"{t}({sig})" for t, sig in shown)
    remaining = len(notable) - len(shown)
    if remaining > 0:
        notable_str += f" 외 {remaining}개"
    return notable_str


def build_message(client, date_str: str | None, max_len: int) -> str:
    portfolio = fetch_portfolio_summary(client, date_str)
    if not portfolio:
        return "포트폴리오 분석 데이터가 아직 없습니다. daily-analysis 실행 여부를 확인해주세요."

    actual_date = portfolio["date"]
    summary = portfolio["summary"] or ""
    signals = fetch_signals(client, actual_date)

    date_label = dt.date.fromisoformat(actual_date).strftime("%m/%d")
    header = f"[포트폴리오 {date_label}] "

    # 종목이 아주 많아도 tail이 무한정 늘어나지 않도록 max_items를 점점
    # 줄여가며, 요약 문장에 최소한의 자리(MIN_SUMMARY_BUDGET)를 확보한다.
    MIN_SUMMARY_BUDGET = 40
    for max_items in (6, 4, 2, 1, 0):
        notable_str = build_notable_str(signals, max_items=max_items) if max_items else "특이 신호 없음"
        tail = f" 주목: {notable_str}"
        budget_for_summary = max_len - len(header) - len(tail)
        if budget_for_summary >= MIN_SUMMARY_BUDGET or max_items == 0:
            break

    if budget_for_summary < 0:
        return truncate(header + tail.strip(), max_len)

    summary_part = truncate(summary, budget_for_summary) if budget_for_summary < len(summary) else summary
    message = f"{header}{summary_part}{tail}"
    return truncate(message, max_len)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", help="YYYY-MM-DD (기본: 오늘, KST 기준)")
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
