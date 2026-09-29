"""Send the briefing via Amazon SNS."""
from __future__ import annotations

from .config import Config
from .utils import log, timed


def publish(cfg: Config, subject: str, body: str) -> str:
    if cfg.dry_run or not cfg.sns_topic_arn:
        log("sns.skipped", reason="dry_run" if cfg.dry_run else "SNS_TOPIC_ARN not set")
        return "skipped"
    import boto3
    # SNS is regional: the region is encoded in the topic ARN (arn:aws:sns:<region>:...)
    region = cfg.sns_topic_arn.split(":")[3]
    with timed("sns.publish", topic_arn=cfg.sns_topic_arn):
        resp = boto3.client("sns", region_name=region).publish(
            TopicArn=cfg.sns_topic_arn, Subject=subject, Message=body)
    log("sns.published", message_id=resp["MessageId"])
    return resp["MessageId"]
