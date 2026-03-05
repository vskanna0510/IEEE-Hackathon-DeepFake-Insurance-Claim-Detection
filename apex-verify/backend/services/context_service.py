"""
Context Verification Service

Validates contextual consistency of a claim by:
1. Extracting GPS coordinates and capture timestamp from EXIF
2. Querying Open-Meteo historical weather API (free, no API key required)
3. Scoring consistency between weather conditions and claim type keywords

Returns a context_consistency_score in [0, 1] — higher means more consistent.
"""
from __future__ import annotations

import asyncio
import math
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple

import httpx


# Open-Meteo free historical weather API — no key required
_WEATHER_API = "https://archive-api.open-meteo.com/v1/archive"
_CACHE: Dict[str, Dict] = {}


def _parse_gps(exif: Dict[str, Any]) -> Optional[Tuple[float, float]]:
    """Extract (latitude, longitude) from parsed EXIF dict."""
    gps_section = exif.get("GPS", {})
    if not gps_section:
        return None

    def dms_to_decimal(dms, ref) -> Optional[float]:
        try:
            d, m, s = dms
            # piexif stores tuples as (numerator, denominator)
            if isinstance(d, (list, tuple)):
                d = d[0] / d[1]
            if isinstance(m, (list, tuple)):
                m = m[0] / m[1]
            if isinstance(s, (list, tuple)):
                s = s[0] / s[1]
            val = d + m / 60.0 + s / 3600.0
            if ref in ("S", "W"):
                val = -val
            return val
        except Exception:
            return None

    lat_dms = gps_section.get("GPSLatitude")
    lat_ref = gps_section.get("GPSLatitudeRef", "N")
    lon_dms = gps_section.get("GPSLongitude")
    lon_ref = gps_section.get("GPSLongitudeRef", "E")

    if lat_dms and lon_dms:
        lat = dms_to_decimal(lat_dms, lat_ref)
        lon = dms_to_decimal(lon_dms, lon_ref)
        if lat is not None and lon is not None:
            return lat, lon
    return None


def _parse_datetime_from_exif(exif: Dict[str, Any]) -> Optional[datetime]:
    """Extract capture datetime from EXIF."""
    for section in exif.values():
        if not isinstance(section, dict):
            continue
        for key in ("DateTimeOriginal", "DateTimeDigitized", "DateTime"):
            val = section.get(key)
            if isinstance(val, str) and val.strip():
                try:
                    return datetime.strptime(val.strip(), "%Y:%m:%d %H:%M:%S")
                except ValueError:
                    try:
                        return datetime.strptime(val.strip()[:10], "%Y-%m-%d")
                    except ValueError:
                        pass
    return None


async def _fetch_weather(lat: float, lon: float, date: datetime) -> Optional[Dict]:
    """Fetch historical weather data from Open-Meteo archive API."""
    date_str = date.strftime("%Y-%m-%d")
    cache_key = f"{lat:.3f},{lon:.3f},{date_str}"

    if cache_key in _CACHE:
        return _CACHE[cache_key]

    params = {
        "latitude": round(lat, 4),
        "longitude": round(lon, 4),
        "start_date": date_str,
        "end_date": date_str,
        "daily": "precipitation_sum,weathercode,windspeed_10m_max",
        "timezone": "auto",
    }

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get(_WEATHER_API, params=params)
            if r.status_code == 200:
                data = r.json().get("daily", {})
                result = {
                    "precipitation_mm": (data.get("precipitation_sum") or [None])[0],
                    "weather_code": (data.get("weathercode") or [None])[0],
                    "wind_speed_kmh": (data.get("windspeed_10m_max") or [None])[0],
                    "date": date_str,
                }
                _CACHE[cache_key] = result
                return result
    except Exception:
        pass
    return None


# WMO weather codes that indicate relevant disaster types
_FLOOD_CODES = {55, 65, 67, 75, 77, 82, 85, 86, 95, 96, 99}
_STORM_CODES = {51, 53, 55, 61, 63, 65, 67, 71, 73, 75, 80, 81, 82, 95, 96, 99}
_FIRE_CODES: set = set()  # Fire is not in WMO codes; use wind + dry proxy


def _score_weather_claim_consistency(
    weather: Dict,
    claim_keywords: list[str],
) -> Tuple[float, str]:
    """
    Score how consistent the weather was with the claim type.
    Returns (score [0,1], explanation).
    """
    code = weather.get("weather_code")
    rain = weather.get("precipitation_mm") or 0.0
    wind = weather.get("wind_speed_kmh") or 0.0

    keywords_lower = [k.lower() for k in claim_keywords]

    def has_kw(*words) -> bool:
        return any(w in k for k in keywords_lower for w in words)

    score = 0.5  # neutral default
    explanation = "No specific weather validation performed."

    if has_kw("flood", "water", "rain", "storm"):
        if code in _FLOOD_CODES or rain > 10.0:
            score = 0.85
            explanation = f"Weather data confirms precipitation ({rain:.1f}mm) consistent with flood/storm claim."
        elif rain < 1.0 and code not in _STORM_CODES:
            score = 0.15
            explanation = f"No significant rainfall ({rain:.1f}mm) recorded — inconsistent with flood/storm claim."
        else:
            score = 0.55
            explanation = "Moderate precipitation recorded; partial consistency with claim."

    elif has_kw("wind", "hurricane", "typhoon", "cyclone"):
        if wind > 50:
            score = 0.85
            explanation = f"High wind speed ({wind:.1f}km/h) recorded — consistent with wind damage claim."
        elif wind < 20:
            score = 0.15
            explanation = f"Low wind speed ({wind:.1f}km/h) — inconsistent with wind damage claim."
        else:
            score = 0.55
            explanation = f"Moderate wind ({wind:.1f}km/h) — partially consistent."

    elif has_kw("fire", "burn", "smoke", "ember"):
        # Fire likely with low rainfall + high wind
        if rain < 0.5 and wind > 20:
            score = 0.80
            explanation = "Dry, windy conditions consistent with fire damage claim."
        elif rain > 5.0:
            score = 0.20
            explanation = "Heavy rainfall recorded — inconsistent with fire damage claim."
        else:
            score = 0.50
            explanation = "Weather conditions are ambiguous relative to fire claim."

    elif has_kw("hail"):
        if code in {96, 99}:
            score = 0.90
            explanation = "Hailstorm weather code confirmed — highly consistent with hail claim."
        else:
            score = 0.25
            explanation = "No hail weather code recorded — inconsistent with claim."

    return score, explanation


async def run(exif: Dict[str, Any], claim_keywords: list[str] | None = None) -> Dict[str, Any]:
    """
    Execute full context verification.

    Args:
        exif: Parsed EXIF dict from ingestion
        claim_keywords: Optional list of claim-type keywords (e.g. ["flood", "damage"])

    Returns context consistency report.
    """
    if claim_keywords is None:
        claim_keywords = []

    gps = _parse_gps(exif)
    capture_dt = _parse_datetime_from_exif(exif)

    report: Dict[str, Any] = {
        "context_consistency_score": 0.5,  # neutral
        "gps_found": gps is not None,
        "timestamp_found": capture_dt is not None,
        "weather_data": None,
        "explanation": "Insufficient EXIF data for context verification.",
    }

    if gps is None or capture_dt is None:
        if gps is None and capture_dt is None:
            report["context_consistency_score"] = 0.45
            report["explanation"] = "No GPS or timestamp found in EXIF — cannot perform context validation."
        elif gps is None:
            report["context_consistency_score"] = 0.48
            report["explanation"] = "No GPS coordinates in EXIF — location-based verification skipped."
        else:
            report["context_consistency_score"] = 0.48
            report["explanation"] = "No capture timestamp in EXIF — time-based verification skipped."
        return report

    lat, lon = gps
    report["gps_coordinates"] = {"lat": round(lat, 5), "lon": round(lon, 5)}
    report["capture_datetime"] = capture_dt.isoformat()

    weather = await _fetch_weather(lat, lon, capture_dt)

    if weather is None:
        report["context_consistency_score"] = 0.50
        report["explanation"] = "Could not retrieve weather data (API unavailable or date out of range)."
        return report

    report["weather_data"] = weather

    if claim_keywords:
        score, explanation = _score_weather_claim_consistency(weather, claim_keywords)
        report["context_consistency_score"] = round(score, 3)
        report["explanation"] = explanation
    else:
        report["context_consistency_score"] = 0.55
        report["explanation"] = "Weather data retrieved but no claim keywords provided for matching."

    return report


__all__ = ["run"]
