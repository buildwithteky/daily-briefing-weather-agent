"""Weather via Open-Meteo (free, no API key)."""
from __future__ import annotations

import urllib.parse
from datetime import datetime
from zoneinfo import ZoneInfo

from .config import Config
from .utils import SourceResult, http_get_json, log, timed

WMO = {0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast", 45: "Fog",
       48: "Rime fog", 51: "Light drizzle", 53: "Drizzle", 55: "Heavy drizzle",
       61: "Light rain", 63: "Rain", 65: "Heavy rain", 71: "Light snow", 73: "Snow",
       75: "Heavy snow", 80: "Rain showers", 81: "Rain showers", 82: "Violent rain showers",
       95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with heavy hail"}


def get_weather(cfg: Config) -> SourceResult:
    result = SourceResult("weather")
    try:
        with timed("data.weather", city=cfg.city):
            geo = http_get_json(cfg.geocoding_url + "?" + urllib.parse.urlencode(
                {"name": cfg.city, "count": 1}), cfg.http_timeout)
            if not geo.get("results"):
                raise ValueError("City not found: " + cfg.city)
            place = geo["results"][0]
            params = {
                "latitude": place["latitude"], "longitude": place["longitude"],
                "current": "temperature_2m,apparent_temperature,relative_humidity_2m,"
                           "weather_code,wind_speed_10m",
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max",
                "temperature_unit": cfg.units, "timezone": cfg.timezone, "forecast_days": 1,
            }
            w = http_get_json(cfg.weather_url + "?" + urllib.parse.urlencode(params),
                              cfg.http_timeout)
            cur, day = w["current"], w["daily"]
            result.data = {
                "city": place["name"], "country": place.get("country"),
                "observed_at": cur["time"],
                "condition": WMO.get(cur["weather_code"], "Code %s" % cur["weather_code"]),
                "temperature": cur["temperature_2m"],
                "feels_like": cur["apparent_temperature"],
                "humidity_percent": cur["relative_humidity_2m"],
                "wind_kmh": cur["wind_speed_10m"],
                "high": day["temperature_2m_max"][0], "low": day["temperature_2m_min"][0],
                "rain_chance_percent": day["precipitation_probability_max"][0],
                "unit": "°C" if cfg.units == "celsius" else "°F",
            }
            result.status = "ok"
            # Staleness check: observation older than the configured limit
            observed = datetime.fromisoformat(cur["time"]).replace(tzinfo=ZoneInfo(cfg.timezone))
            age_min = (datetime.now(ZoneInfo(cfg.timezone)) - observed).total_seconds() / 60
            if age_min > cfg.stale_after_minutes:
                result.status = "stale"
                result.note = "Observation is %d minutes old" % age_min
    except Exception as exc:  # any failure -> mark unavailable, keep going
        result.status, result.error = "unavailable", "%s: %s" % (type(exc).__name__, exc)
        log("data.weather.failed", level="WARNING", error=result.error)
    return result
