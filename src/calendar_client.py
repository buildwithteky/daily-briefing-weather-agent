"""Today's events from a Google Calendar 'secret address in iCal format' (no OAuth needed).

Get the link: Google Calendar > Settings > your calendar > Integrate calendar >
"Secret address in iCal format". Treat it like a password. It is never logged.
Recurring events: DAILY/WEEKLY/MONTHLY/YEARLY rules are handled (INTERVAL, BYDAY, UNTIL,
EXDATE). Unusual rules (COUNT, BYSETPOS...) are approximate; the note says so.
"""
from __future__ import annotations

import re
from datetime import date, datetime, timedelta, timezone
from typing import List, Optional
from zoneinfo import ZoneInfo

from .config import Config
from .utils import SourceResult, http_get, log, timed

DAYS = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]


def _unfold(text: str) -> List[str]:
    return re.sub(r"\r?\n[ \t]", "", text).splitlines()


def _parse_dt(prop: str, value: str, tz: ZoneInfo):
    """Return (aware_or_None_for_allday, date, is_allday)."""
    if "VALUE=DATE" in prop or len(value) == 8:
        d = datetime.strptime(value[:8], "%Y%m%d").date()
        return None, d, True
    m = re.search(r"TZID=([^;:]+)", prop)
    if value.endswith("Z"):
        dt = datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
    else:
        dt = datetime.strptime(value[:15], "%Y%m%dT%H%M%S").replace(
            tzinfo=ZoneInfo(m.group(1)) if m else tz)
    local = dt.astimezone(tz)
    return local, local.date(), False


def _events(text: str, tz: ZoneInfo) -> List[dict]:
    events, cur = [], None
    for line in _unfold(text):
        if line == "BEGIN:VEVENT":
            cur = {"exdates": set()}
        elif line == "END:VEVENT" and cur is not None:
            if "start" in cur and "SUMMARY" in cur:
                events.append(cur)
            cur = None
        elif cur is not None and ":" in line:
            prop, value = line.split(":", 1)
            name = prop.split(";")[0]
            try:
                if name == "DTSTART":
                    cur["start"], cur["start_date"], cur["allday"] = _parse_dt(prop, value, tz)
                elif name == "DTEND":
                    cur["end"], cur["end_date"], _ = _parse_dt(prop, value, tz)
                elif name == "EXDATE":
                    for v in value.split(","):
                        cur["exdates"].add(_parse_dt(prop, v, tz)[1])
                elif name == "RRULE":
                    cur["rrule"] = dict(kv.split("=", 1) for kv in value.split(";") if "=" in kv)
                elif name == "SUMMARY":
                    cur["SUMMARY"] = value.replace("\\,", ",").replace("\;", ";").replace("\\n", " ").strip()
                elif name == "STATUS" and value == "CANCELLED":
                    cur["cancelled"] = True
            except (ValueError, KeyError):
                cur = None if name == "DTSTART" else cur
    return events


def _occurs_on(ev: dict, day: date) -> Optional[bool]:
    """True/False, or None if the recurrence rule is only approximated."""
    s = ev["start_date"]
    span = (ev.get("end_date", s) - s).days if ev["allday"] else 0
    if "rrule" not in ev:
        return s <= day <= s + timedelta(days=max(span - 1, 0)) if ev["allday"] else s == day
    r = ev["rrule"]
    if day < s or day in ev["exdates"]:
        return False
    if "UNTIL" in r and day > _parse_dt("", r["UNTIL"], ZoneInfo("UTC"))[1]:
        return False
    n = int(r.get("INTERVAL", 1))
    f = r.get("FREQ")
    if f == "DAILY":
        ok = (day - s).days % n == 0
    elif f == "WEEKLY":
        byday = [DAYS.index(d[-2:]) for d in r["BYDAY"].split(",")] if "BYDAY" in r else [s.weekday()]
        ok = day.weekday() in byday and (((day - timedelta(days=day.weekday())) - (s - timedelta(days=s.weekday()))).days // 7) % n == 0
    elif f == "MONTHLY":
        ok = day.day == s.day and ((day.year - s.year) * 12 + day.month - s.month) % n == 0
    elif f == "YEARLY":
        ok = (day.month, day.day) == (s.month, s.day)
    else:
        return None
    return ok and (None if ("COUNT" in r or "BYSETPOS" in r) and ok else ok)


def get_calendar(cfg: Config) -> SourceResult:
    result = SourceResult("calendar")
    try:
        with timed("data.calendar"):
            tz = ZoneInfo(cfg.timezone)
            today = datetime.now(tz).date()
            raw = http_get(cfg.calendar_ics_url, cfg.http_timeout * 2).decode("utf-8", "replace")
            if "BEGIN:VCALENDAR" not in raw:
                raise ValueError("URL did not return an iCal calendar (check the secret address)")
            rows, approx = [], False
            for ev in _events(raw, tz):
                if ev.get("cancelled"):
                    continue
                hit = _occurs_on(ev, today)
                if hit is None:
                    approx = True
                if hit:
                    when = "All day" if ev["allday"] else ev["start"].strftime("%H:%M")
                    rows.append((when if ev["allday"] else ev["start"].strftime("%H:%M"), ev["SUMMARY"]))
            rows.sort(key=lambda r: ("0" if r[0] == "All day" else "1") + r[0])
            result.data = ["%s - %s" % r for r in rows] or ["No events today"]
            result.status = "ok"
            if approx:
                result.note = "Some recurring events use rules that are only approximated"
            log("data.calendar.parsed", events_today=len(rows))
    except Exception as exc:
        result.error = "%s: %s" % (type(exc).__name__, str(exc)[:200])
        log("data.calendar.failed", level="WARNING", error=result.error)
    return result
