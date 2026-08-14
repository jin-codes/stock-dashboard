#!/usr/bin/env python3
"""Kakao '나에게 보내기' API에 넣을 template_object JSON을 만든다.

daily-analysis.yml의 "Send Kakao daily summary" 스텝에서 사용. YAML
run 블록 안에 파이썬 코드를 직접 인라인하면 들여쓰기 때문에 YAML/파이썬
양쪽에서 문법 오류가 나기 쉬워서, 별도 스크립트로 분리했다.

/tmp/kakao_message.txt (build_kakao_summary.py가 만든 메시지)를 읽고,
REPO_URL 환경변수와 합쳐 /tmp/template_object.json으로 저장한다.
"""
import json
import os

MESSAGE_PATH = "/tmp/kakao_message.txt"
OUTPUT_PATH = "/tmp/template_object.json"


def main():
    with open(MESSAGE_PATH, encoding="utf-8") as f:
        message = f.read().strip()

    repo_url = os.environ.get("REPO_URL", "https://github.com")
    template = {
        "object_type": "text",
        "text": message,
        "link": {"web_url": repo_url, "mobile_web_url": repo_url},
    }
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(template, f, ensure_ascii=False)


if __name__ == "__main__":
    main()
