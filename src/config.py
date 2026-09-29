"""Configuration: everything is read from environment variables."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List


def _list(value: str, sep: str = ",") -> List[str]:
    return [v.strip() for v in value.split(sep) if v.strip()]


@dataclass
class Config:
    city: str = "Indore"
    timezone: str = "Asia/Kolkata"
    units: str = "celsius"  # celsius | fahrenheit
    user_name: str = ""  # empty = greet without a name
    topics: List[str] = field(default_factory=lambda: ["weather", "aws", "tech", "calendar", "tasks", "billing"])
    daily_tasks: List[str] = field(default_factory=list)

    bedrock_region: str = "us-east-1"
    model_id: str = "us.amazon.nova-lite-v1:0"
    max_tokens: int = 800
    temperature: float = 0.3

    geocoding_url: str = "https://geocoding-api.open-meteo.com/v1/search"
    weather_url: str = "https://api.open-meteo.com/v1/forecast"
    aws_feed_url: str = "https://aws.amazon.com/about-aws/whats-new/recent/feed/"
    hn_api_url: str = "https://hacker-news.firebaseio.com/v0"
    tech_feed_url: str = "https://hnrss.org/frontpage"  # backup if the HN API fails
    calendar_ics_url: str = ""  # secret iCal address of your Google Calendar
    max_news_items: int = 5
    http_timeout: int = 8
    stale_after_minutes: int = 180

    gmail_user: str = ""  # set to enable "tasks from email"
    gmail_label: str = "INBOX"  # mailbox/label to scan (INBOX = everything recent; or e.g. "tasks")
    gmail_password_param: str = "/daily-briefing/gmail-app-password"  # SSM SecureString name
    email_lookback_hours: int = 24
    max_emails: int = 30

    sns_topic_arn: str = ""
    email_subject_prefix: str = "Daily Briefing"
    notify_on_success: bool = True  # email the briefing every run
    notify_on_failure: bool = True  # email an alert when a run fails
    dry_run: bool = False  # True = never call SNS

    @classmethod
    def from_env(cls) -> "Config":
        d = cls()
        e = os.environ.get
        return cls(
            city=e("CITY", d.city),
            timezone=e("TIMEZONE", d.timezone),
            units=e("TEMP_UNITS", d.units).lower(),
            user_name=e("USER_NAME", d.user_name),
            topics=[t.lower() for t in _list(e("BRIEFING_TOPICS", ",".join(d.topics)))],
            daily_tasks=_list(e("DAILY_TASKS", ""), ";"),
            bedrock_region=e("BEDROCK_REGION", d.bedrock_region),
            model_id=e("MODEL_ID", d.model_id),
            max_tokens=int(e("MAX_TOKENS", d.max_tokens)),
            temperature=float(e("TEMPERATURE", d.temperature)),
            geocoding_url=e("GEOCODING_URL", d.geocoding_url),
            weather_url=e("WEATHER_URL", d.weather_url),
            aws_feed_url=e("AWS_FEED_URL", d.aws_feed_url),
            hn_api_url=e("HN_API_URL", d.hn_api_url),
            tech_feed_url=e("TECH_FEED_URL", d.tech_feed_url),
            calendar_ics_url=e("CALENDAR_ICS_URL", ""),
            max_news_items=int(e("MAX_NEWS_ITEMS", d.max_news_items)),
            http_timeout=int(e("HTTP_TIMEOUT", d.http_timeout)),
            stale_after_minutes=int(e("STALE_AFTER_MINUTES", d.stale_after_minutes)),
            gmail_user=e("GMAIL_USER", ""),
            gmail_label=e("GMAIL_LABEL", d.gmail_label),
            gmail_password_param=e("GMAIL_PASSWORD_PARAM", d.gmail_password_param),
            email_lookback_hours=int(e("EMAIL_LOOKBACK_HOURS", d.email_lookback_hours)),
            max_emails=int(e("MAX_EMAILS", d.max_emails)),
            sns_topic_arn=e("SNS_TOPIC_ARN", ""),
            email_subject_prefix=e("EMAIL_SUBJECT_PREFIX", d.email_subject_prefix),
            dry_run=e("DRY_RUN", "false").lower() in ("1", "true", "yes"),
        )
