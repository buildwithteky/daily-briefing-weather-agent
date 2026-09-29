"""Saves one record per run to DynamoDB so the dashboard can show real history."""
from __future__ import annotations

import json
import os
import time
from typing import Any, Dict

from .utils import log


def save_run(record: Dict[str, Any]) -> None:
    """Never raises: history is nice-to-have and must not break the briefing."""
    try:
        import boto3
        region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION") or "us-east-1"
        item = {
            "pk": {"S": "RUN"},
            "startedAt": {"S": record["startedAt"]},
            "status": {"S": record["status"]},
            "trigger": {"S": record["trigger"]},
            "durationMs": {"N": str(record["durationMs"])},
            "aiUsed": {"BOOL": bool(record.get("aiUsed"))},
            "sent": {"BOOL": bool(record.get("sent"))},
            "sources": {"S": json.dumps(record.get("sources", {}))},
            "ttl": {"N": str(int(time.time()) + 30 * 86400)},  # auto-delete after 30 days
        }
        for key in ("messageId", "error", "subject", "body"):
            if record.get(key):
                item[key] = {"S": str(record[key])[:300000]}
        boto3.client("dynamodb", region_name=region).put_item(
            TableName=os.environ.get("RUNS_TABLE", "daily-briefing-runs"), Item=item)
        log("run.saved", status=record["status"])
    except Exception as exc:
        log("run.save_failed", level="WARNING", error="%s: %s" % (type(exc).__name__, str(exc)[:200]))
