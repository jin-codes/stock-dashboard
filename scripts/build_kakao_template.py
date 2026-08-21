#!/usr/bin/env python3
"""Build the template_object JSON for the Kakao "message to me" API.

Used by the "Send Kakao daily summary" step in daily-analysis.yml. Inlining
Python directly in a YAML run block gets fragile fast (indentation trips up
both YAML and Python), so this is split out into its own script.

Reads /tmp/kakao_message.txt (the message built by build_kakao_summary.py),
combines it with the REPO_URL environment variable, and writes the result
to /tmp/template_object.json.
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
