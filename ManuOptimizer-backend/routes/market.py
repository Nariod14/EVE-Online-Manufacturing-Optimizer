"""Market history from ESI, used to suggest a blueprint's max (units sold per plan).

ESI: GET /markets/{region_id}/history/?type_id=  (public, no login needed)
Each entry is one day: {"date": "2026-11-15", "volume": 123, "average": ..., ...}.
Days with no trades are missing from the list, so they count as zero volume.
ESI refreshes history once a day, so it is cached for a few hours.
"""
from datetime import date, datetime, timedelta, timezone
import logging
import math
import time

import requests

logger = logging.getLogger(__name__)

ESI_HISTORY_URL = "https://esi.evetech.net/latest/markets/{region_id}/history/"
HISTORY_CACHE_TTL = 6 * 3600   # seconds
DEFAULT_WINDOW_DAYS = 30       # days of history averaged
DEFAULT_SUGGEST_DAYS = 3       # suggested max = this many days of average volume

_history_cache = {}            # (region_id, type_id) -> {"timestamp", "etag", "history"}


def fetch_market_history(region_id, type_id, headers, retries=2):
    """Daily history list for one item in one region, or None if ESI has none / fails."""
    key = (int(region_id), int(type_id))
    cached = _history_cache.get(key)
    if cached and time.time() - cached["timestamp"] < HISTORY_CACHE_TTL:
        return cached["history"]

    local_headers = dict(headers or {})
    if cached and cached.get("etag"):
        local_headers["If-None-Match"] = cached["etag"]
    url = ESI_HISTORY_URL.format(region_id=key[0])

    for attempt in range(retries + 1):
        try:
            response = requests.get(url, params={"type_id": key[1]}, headers=local_headers, timeout=15)
            if response.status_code == 304 and cached:
                cached["timestamp"] = time.time()
                return cached["history"]
            if response.status_code in (400, 404):
                logger.warning(f"No market history for type_id {key[1]} in region {key[0]} ({response.status_code})")
                return None
            response.raise_for_status()
            history = response.json()
            _history_cache[key] = {
                "timestamp": time.time(),
                "etag": response.headers.get("ETag"),
                "history": history,
            }
            return history
        except Exception as e:
            logger.error(f"Market history attempt {attempt + 1} for type_id {key[1]} failed: {e}")
            time.sleep(1)
    return None


def average_daily_volume(history, window_days=DEFAULT_WINDOW_DAYS, today=None):
    """Average units traded per day over the last `window_days` complete days.

    The window ends yesterday (UTC); today's trading is not in ESI history yet.
    Missing days count as zero. Returns None when there is no history at all.
    """
    if history is None:
        return None
    window_days = max(1, int(window_days))
    today = today or datetime.now(timezone.utc).date()
    first = today - timedelta(days=window_days)
    total = 0
    for entry in history:
        try:
            day = date.fromisoformat(str(entry.get("date")))
        except (TypeError, ValueError):
            continue
        if first <= day < today:
            total += max(0, int(entry.get("volume") or 0))
    return total / window_days


def suggested_max(avg_volume, days=DEFAULT_SUGGEST_DAYS):
    """Units you could expect to sell in `days` days, rounded down. None if unknown."""
    if avg_volume is None:
        return None
    return int(math.floor(max(0.0, float(avg_volume)) * max(0.0, float(days)) + 1e-9))
