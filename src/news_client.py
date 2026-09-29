"""News sources: AWS What's New (RSS) and tech news (Hacker News API)."""
from __future__ import annotations

import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor

from .config import Config
from .utils import SourceResult, http_get, http_get_json, log, timed


def _fetch_rss(name: str, url: str, cfg: Config) -> SourceResult:
    result = SourceResult(name)
    try:
        with timed("data." + name, url=url):
            root = ET.fromstring(http_get(url, cfg.http_timeout))
            items = []
            for item in root.iter("item"):
                items.append({"title": (item.findtext("title") or "").strip(),
                              "link": (item.findtext("link") or "").strip(),
                              "published": (item.findtext("pubDate") or "").strip()})
                if len(items) >= cfg.max_news_items:
                    break
            if not items:
                raise ValueError("Feed contained no items")
            result.data, result.status = items, "ok"
    except Exception as exc:
        result.error = "%s: %s" % (type(exc).__name__, exc)
        log("data." + name + ".failed", level="WARNING", error=result.error)
    return result


def get_aws_news(cfg: Config) -> SourceResult:
    return _fetch_rss("aws_announcements", cfg.aws_feed_url, cfg)


def _hn_api(cfg: Config) -> SourceResult:
    """Official Hacker News API: top story ids, then each story (fetched in parallel)."""
    result = SourceResult("tech_news")
    with timed("data.tech_news.hn_api"):
        ids = http_get_json(cfg.hn_api_url + "/topstories.json", cfg.http_timeout)[: cfg.max_news_items]

        def story(i):
            d = http_get_json("%s/item/%s.json" % (cfg.hn_api_url, i), cfg.http_timeout)
            return {"title": d["title"], "link": d.get("url") or "https://news.ycombinator.com/item?id=%s" % i}

        with ThreadPoolExecutor(max_workers=5) as pool:
            items = list(pool.map(story, ids))
    if not items:
        raise ValueError("HN API returned no stories")
    result.data, result.status = items, "ok"
    return result


def get_tech_news(cfg: Config) -> SourceResult:
    try:
        return _hn_api(cfg)
    except Exception as exc:  # fall back to the RSS mirror
        log("data.tech_news.hn_api_failed", level="WARNING", error="%s: %s" % (type(exc).__name__, exc))
        return _fetch_rss("tech_news", cfg.tech_feed_url, cfg)
