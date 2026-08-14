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


def build_message(client, date_str: str | None, max_len: int) -> str:
    portfolio = fetch_portfolio_summary(client, date_str)
    if not portfolio:
        return "포트폴리오 분석 데이터가 아직 없습니다. daily-analysis 실행 여부를 확인해주세요."

    actual_date = portfolio["date"]
    summary = portfolio["summary"] or ""
    signals = fetch_signals(client, actual_date)

    notable = [f"{r['ticker']}({r['signal']})" for r in signals if r["signal"] != NEUTRAL_SIGNAL]
    notable_str = ", ".join(notable) if notable else "특이 신호 없음"

    date_label = dt.date.fromisoformat(actual_date).strftime("%m/%d")
    header = f"[포트폴리오 {date_label}] "
    tail = f" 주목: {notable_str}"

    budget_for_summary = max_len - len(header) - len(tail)
    if budget_for_summary < 0:
        # 종목 목록만으로도 넘치면 종목 목록부터 자른다
        full = truncate(header + tail.strip(), max_len)
        return full

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
