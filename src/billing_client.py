"""AWS spend and credits via Cost Explorer (ce:GetCostAndUsage / GetCostForecast).

Limits (be honest in the email): Cost Explorer data lags up to ~24 h, and the REMAINING
credit balance is not available through any API (see console: Billing > Credits).
Each Cost Explorer API request costs about $0.01; this makes about 4 calls per run.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, List

from .config import Config
from .utils import SourceResult, log, timed

NOT_CREDIT = {"Not": {"Dimensions": {"Key": "RECORD_TYPE", "Values": ["Credit", "Refund"]}}}
ONLY_CREDIT = {"Dimensions": {"Key": "RECORD_TYPE", "Values": ["Credit"]}}


def _amount(group_or_total: Dict[str, Any]) -> float:
    return float(group_or_total["UnblendedCost"]["Amount"])


def summarize(ce, today: date) -> Dict[str, Any]:
    start, end = today.replace(day=1), today + timedelta(days=1)  # End is exclusive
    period = {"Start": start.isoformat(), "End": end.isoformat()}

    usage = ce.get_cost_and_usage(TimePeriod=period, Granularity="MONTHLY", Metrics=["UnblendedCost"],
                                  Filter=NOT_CREDIT, GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}])
    groups = [(g["Keys"][0], _amount(g["Metrics"])) for r in usage["ResultsByTime"] for g in r["Groups"]]
    gross = sum(a for _, a in groups)
    top = [{"service": k, "usd": round(a, 2)} for k, a in sorted(groups, key=lambda x: -x[1])[:5] if a >= 0.01]

    cred = ce.get_cost_and_usage(TimePeriod=period, Granularity="MONTHLY", Metrics=["UnblendedCost"], Filter=ONLY_CREDIT)
    credits = sum(_amount(r["Total"]) for r in cred["ResultsByTime"])  # negative = credit applied

    yesterday = None
    if today.day > 1:
        y = ce.get_cost_and_usage(TimePeriod={"Start": (today - timedelta(days=1)).isoformat(), "End": today.isoformat()},
                                  Granularity="DAILY", Metrics=["UnblendedCost"], Filter=NOT_CREDIT)
        yesterday = round(sum(_amount(r["Total"]) for r in y["ResultsByTime"]), 2)

    forecast = None
    try:  # needs enough history; skip quietly if not available
        f = ce.get_cost_forecast(TimePeriod={"Start": today.isoformat(), "End": (today.replace(day=28) + timedelta(days=4)).replace(day=1).isoformat()},
                                 Metric="UNBLENDED_COST", Granularity="MONTHLY")
        forecast = round(gross + float(f["Total"]["Amount"]), 2)
    except Exception as exc:
        log("data.billing.forecast_skipped", error=type(exc).__name__)

    return {"month": start.strftime("%B %Y"), "currency": "USD",
            "month_to_date_usage": round(gross, 2), "credits_applied_this_month": round(-credits, 2),
            "month_to_date_net_charge": round(gross + credits, 2), "yesterday_usage": yesterday,
            "forecast_month_end_usage": forecast, "top_services": top,
            "limits": "Data can lag up to 24 hours. Remaining credit balance is not available via API; "
                      "see the AWS console under Billing > Credits."}


def get_billing(cfg: Config) -> SourceResult:
    result = SourceResult("aws_billing")
    try:
        import boto3
        from datetime import datetime
        from zoneinfo import ZoneInfo
        with timed("data.billing"):
            ce = boto3.client("ce", region_name="us-east-1")  # Cost Explorer lives in us-east-1
            result.data = summarize(ce, datetime.now(ZoneInfo("UTC")).date())
            result.status = "ok"
    except Exception as exc:
        result.error = "%s: %s" % (type(exc).__name__, str(exc)[:200])
        log("data.billing.failed", level="WARNING", error=result.error)
    return result
