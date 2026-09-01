"""Pull the daily weather archive for Chicago and fix the study window.

Writes data/weather_daily.csv. The window ends on the last day for which the
archive returns a non-null temperature_2m_max; trailing null days are trimmed.
An interior null that survives three attempts is halt H3.
"""

from __future__ import annotations

import csv
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
ENDPOINT = "https://archive-api.open-meteo.com/v1/archive"
START = "2019-01-01"
END = "2026-08-31"
TIMEOUT = 180
RETRIES = 3
BACKOFF = 10

VARS = [
    "temperature_2m_max",
    "temperature_2m_min",
    "temperature_2m_mean",
    "precipitation_sum",
    "rain_sum",
    "snowfall_sum",
    "wind_speed_10m_max",
]

PARAMS = {
    "latitude": 41.8781,
    "longitude": -87.6298,
    "start_date": START,
    "end_date": END,
    "daily": ",".join(VARS),
    "timezone": "America/Chicago",
}


def fetch() -> dict:
    last = None
    for attempt in range(1, RETRIES + 1):
        try:
            r = requests.get(ENDPOINT, params=PARAMS, timeout=TIMEOUT)
            if r.status_code == 200:
                return r.json()["daily"]
            last = f"HTTP {r.status_code}: {r.text[:500]}"
        except (requests.RequestException, KeyError, ValueError) as exc:
            last = f"{type(exc).__name__}: {exc}"
        print(f"  attempt {attempt} failed: {last}", file=sys.stderr)
        if attempt < RETRIES:
            time.sleep(BACKOFF)
    raise RuntimeError(last or "unknown failure")


def main() -> int:
    for attempt in range(1, RETRIES + 1):
        try:
            daily = fetch()
        except RuntimeError as exc:
            print(f"H3: weather archive unreachable: {exc}", file=sys.stderr)
            return 3

        days = daily["time"]
        tmax = daily["temperature_2m_max"]

        last_ok = max(
            (i for i, v in enumerate(tmax) if v is not None), default=-1
        )
        if last_ok < 0:
            print("H3: temperature_2m_max is null for every day in the window.",
                  file=sys.stderr)
            return 3

        trimmed_days = days[: last_ok + 1]
        interior_nulls = [
            trimmed_days[i]
            for i, v in enumerate(tmax[: last_ok + 1])
            if v is None
        ]
        if interior_nulls:
            print(f"  attempt {attempt}: {len(interior_nulls)} interior null "
                  f"temperature_2m_max day(s)", file=sys.stderr)
            if attempt < RETRIES:
                time.sleep(BACKOFF)
                continue
            print("H3: interior gaps persist after 3 retries. Missing dates:",
                  file=sys.stderr)
            for d in interior_nulls:
                print(f"  {d}", file=sys.stderr)
            return 3

        DATA.mkdir(parents=True, exist_ok=True)
        out = DATA / "weather_daily.csv"
        with out.open("w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["day"] + VARS)
            for i, d in enumerate(trimmed_days):
                w.writerow([d] + [daily[v][i] for v in VARS])

        from datetime import date

        y0, m0, d0 = (int(x) for x in START.split("-"))
        y1, m1, d1 = (int(x) for x in trimmed_days[-1].split("-"))
        expected = (date(y1, m1, d1) - date(y0, m0, d0)).days + 1
        assert len(trimmed_days) == expected, (
            f"row count {len(trimmed_days)} != days in window {expected}"
        )

        trailing = len(days) - len(trimmed_days)
        print(f"window {trimmed_days[0]} .. {trimmed_days[-1]}")
        print(f"rows {len(trimmed_days)} (expected {expected})")
        print(f"trailing null days trimmed from {END}: {trailing}")
        nulls = {
            v: sum(1 for x in daily[v][: last_ok + 1] if x is None)
            for v in VARS
        }
        print(f"nulls per variable within window: {nulls}")
        print(f"wrote {out}")
        return 0

    return 3


if __name__ == "__main__":
    raise SystemExit(main())
