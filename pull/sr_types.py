"""Enumerate all-time counts per 311 service-request type, with no date dimension.

Writes data/sr_types.csv with columns sr_type, n.

The primary strategy is a single grouped query over the whole dataset. If that
times out or returns a 5xx after three attempts, the fallback repeats the same
grouped query one calendar year at a time and sums the counts client-side; the
result is still an all-time total per type with no date dimension in the output.
"""

from __future__ import annotations

import csv
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
ENDPOINT = "https://data.cityofchicago.org/resource/v6vf-nfxy.json"
TIMEOUT = 180
RETRIES = 3
BACKOFF = 10
YEARS = range(2019, 2027)


def _get(params: dict) -> list[dict]:
    """One Socrata request with three attempts. Raises on final failure."""
    last = None
    for attempt in range(1, RETRIES + 1):
        try:
            r = requests.get(ENDPOINT, params=params, timeout=TIMEOUT)
            if r.status_code == 200:
                return r.json()
            last = f"HTTP {r.status_code}: {r.text[:500]}"
            if r.status_code < 500:
                raise RuntimeError(f"{r.url}\n{last}")
        except requests.RequestException as exc:
            last = f"{type(exc).__name__}: {exc}"
        print(f"  attempt {attempt} failed: {last}", file=sys.stderr)
        if attempt < RETRIES:
            time.sleep(BACKOFF)
    raise RuntimeError(f"{ENDPOINT} {params}\n{last}")


def primary() -> list[dict]:
    return _get(
        {
            "$select": "sr_type,count(*) AS n",
            "$group": "sr_type",
            "$order": "n DESC",
            "$limit": 5000,
        }
    )


def fallback() -> list[dict]:
    totals: dict[str, int] = {}
    for year in YEARS:
        rows = _get(
            {
                "$select": "sr_type,count(*) AS n",
                "$group": "sr_type",
                "$where": (
                    f"created_date >= '{year}-01-01T00:00:00'"
                    f" AND created_date < '{year + 1}-01-01T00:00:00'"
                ),
                "$limit": 5000,
            }
        )
        for row in rows:
            totals[row["sr_type"]] = totals.get(row["sr_type"], 0) + int(row["n"])
        print(f"  {year}: {len(rows)} types", file=sys.stderr)
        time.sleep(0.5)
    return [{"sr_type": k, "n": v} for k, v in totals.items()]


def main() -> int:
    strategy = "primary"
    try:
        rows = primary()
    except RuntimeError as exc:
        print(f"primary strategy failed:\n{exc}", file=sys.stderr)
        strategy = "fallback"
        try:
            rows = fallback()
        except RuntimeError as exc2:
            print(f"H2: fallback strategy also failed:\n{exc2}", file=sys.stderr)
            return 2

    rows = sorted(
        ({"sr_type": r["sr_type"], "n": int(r["n"])} for r in rows),
        key=lambda r: (-r["n"], r["sr_type"]),
    )
    DATA.mkdir(parents=True, exist_ok=True)
    out = DATA / "sr_types.csv"
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["sr_type", "n"])
        w.writeheader()
        w.writerows(rows)

    print(f"strategy={strategy} types={len(rows)} total={sum(r['n'] for r in rows)}")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
