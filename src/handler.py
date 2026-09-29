"""AWS Lambda entry point. Handler: src.handler.lambda_handler"""
from __future__ import annotations

import time
from datetime import datetime, timezone

from .briefing import build_briefing
from .config import Config
from .notifier import publish
from .remote_settings import apply_remote_settings
from .run_store import save_run
from .utils import log


def lambda_handler(event, context):
    start = time.perf_counter()
    started_at = datetime.now(timezone.utc).isoformat()
    source = (event or {}).get("source", "manual")
    trigger = "scheduled" if source == "eventbridge-scheduler" else "manual"
    request_id = getattr(context, "aws_request_id", "local")
    log("scheduler.invoked", request_id=request_id, source=source, trigger_payload=event)
    cfg = Config.from_env()
    ms = lambda: round((time.perf_counter() - start) * 1000)
    try:
        cfg = apply_remote_settings(cfg)
        log("config.loaded", city=cfg.city, timezone=cfg.timezone, topics=cfg.topics,
            model_id=cfg.model_id, region=cfg.bedrock_region)
        briefing = build_briefing(cfg)
        if cfg.notify_on_success:
            message_id = publish(cfg, briefing["subject"], briefing["body"])
        else:
            message_id = "skipped"
            log("sns.skipped", reason="notify_on_success is off")
        sent = message_id not in ("skipped", None)
        degraded = (not briefing["ai_used"]) or any(v != "ok" for v in briefing["source_status"].values())
        status = ("partial" if degraded else "delivered") if sent else "generated"
        log("run.success", status=status, ai_used=briefing["ai_used"], sources=briefing["source_status"],
            message_id=message_id, duration_ms=ms())
        save_run({"startedAt": started_at, "status": status, "trigger": trigger, "durationMs": ms(),
                  "aiUsed": briefing["ai_used"], "sent": sent, "sources": briefing["source_status"],
                  "messageId": message_id if sent else None, "subject": briefing["subject"],
                  "body": briefing["body"], "error": None if not degraded else
                  "Unavailable: " + ", ".join(k for k, v in briefing["source_status"].items() if v != "ok")
                  + ("" if briefing["ai_used"] else " (AI summary failed, raw data sent)")})
        return {"statusCode": 200, "message_id": message_id, "ai_used": briefing["ai_used"],
                "sources": briefing["source_status"], "subject": briefing["subject"], "body": briefing["body"],
                "duration_ms": ms(), "status": status, "started_at": started_at, "sent": sent}
    except Exception as exc:
        log("run.failed", level="ERROR", error=str(exc), error_type=type(exc).__name__, duration_ms=ms())
        if cfg.notify_on_failure:
            try:
                publish(cfg, "Daily Briefing FAILED", "Today's briefing could not be generated.\n\nError: %s: %s\n\n"
                        "Check CloudWatch log group /aws/lambda/%s" % (type(exc).__name__, exc,
                        getattr(context, "function_name", "daily-briefing-agent")))
            except Exception as alert_exc:
                log("alert.failed", level="ERROR", error=str(alert_exc))
        save_run({"startedAt": started_at, "status": "failed", "trigger": trigger, "durationMs": ms(),
                  "error": "%s: %s" % (type(exc).__name__, str(exc)[:300])})
        raise  # let Lambda record the failure
