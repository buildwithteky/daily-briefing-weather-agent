"""Settings saved from the dashboard (SSM Parameter Store) override the environment defaults.

The dashboard writes JSON to /daily-briefing/settings. Only these keys are honoured:
city, timezone, topics, userName, notifyOnSuccess, notifyOnFailure. If the parameter is missing or unreadable the environment values are used.
"""
from __future__ import annotations

import json
import os
from zoneinfo import ZoneInfo

from .config import Config
from .utils import log

VALID_TOPICS = {"weather", "aws", "tech", "calendar", "tasks", "billing"}


def apply_remote_settings(cfg: Config) -> Config:
    name = os.environ.get("SETTINGS_PARAM", "/daily-briefing/settings")
    try:
        import boto3
        region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION") or "us-east-1"
        raw = boto3.client("ssm", region_name=region).get_parameter(Name=name)["Parameter"]["Value"]
        data = json.loads(raw)
    except Exception as exc:
        log("settings.remote_unavailable", level="INFO", reason=type(exc).__name__)
        return cfg
    if isinstance(data.get("city"), str) and 0 < len(data["city"].strip()) <= 80:
        cfg.city = data["city"].strip()
    if isinstance(data.get("timezone"), str):
        try:
            ZoneInfo(data["timezone"])
            cfg.timezone = data["timezone"]
        except Exception:
            log("settings.bad_timezone", level="WARNING")
    if isinstance(data.get("topics"), list):
        topics = [t for t in data["topics"] if t in VALID_TOPICS]
        if topics:
            cfg.topics = topics
    if isinstance(data.get("userName"), str):
        import re
        cfg.user_name = re.sub(r"[^\w .'-]", "", data["userName"])[:40].strip()  # letters/digits/space only
    for key, attr in (("notifyOnSuccess", "notify_on_success"), ("notifyOnFailure", "notify_on_failure")):
        if isinstance(data.get(key), bool):
            setattr(cfg, attr, data[key])
    log("settings.remote_applied", city=cfg.city, timezone=cfg.timezone, topics=cfg.topics)
    return cfg
