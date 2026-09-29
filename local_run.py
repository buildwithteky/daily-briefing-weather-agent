#!/usr/bin/env python3
"""Local test: generate a briefing right now.

  python local_run.py                 # real weather/news + real Bedrock, prints only
  python local_run.py --send          # also publish to SNS (needs SNS_TOPIC_ARN)
  python local_run.py --no-ai         # skip Bedrock (no AWS creds needed)
  python local_run.py --city Delhi --model-id amazon.nova-lite-v1:0
"""
import argparse
import os

from src.briefing import build_briefing
from src.config import Config
from src.notifier import publish


class NoAI:
    def generate(self, *_):
        raise RuntimeError("--no-ai flag set")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--send", action="store_true", help="publish to SNS")
    p.add_argument("--no-ai", action="store_true", help="skip Bedrock, show fallback format")
    p.add_argument("--city"), p.add_argument("--model-id"), p.add_argument("--region")
    a = p.parse_args()
    if os.path.exists(".env"):  # optional simple KEY=VALUE file
        for line in open(".env"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"'))
    cfg = Config.from_env()
    cfg.city = a.city or cfg.city
    cfg.model_id = a.model_id or cfg.model_id
    cfg.bedrock_region = a.region or cfg.bedrock_region
    cfg.dry_run = not a.send
    b = build_briefing(cfg, NoAI() if a.no_ai else None)
    print("\n" + "=" * 60 + "\nSUBJECT: " + b["subject"] + "\n" + "=" * 60)
    print(b["body"] + "\n" + "=" * 60)
    print("AI used: %s | sources: %s" % (b["ai_used"], b["source_status"]))
    if a.send:
        print("SNS message id:", publish(cfg, b["subject"], b["body"]))


if __name__ == "__main__":
    main()
