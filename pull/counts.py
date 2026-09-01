"""Pull 311 daily counts by service-request type, one calendar month at a time.

Writes data/311_daily_by_type.csv with columns day, sr_type, n.

Primary strategy: a grouped count by type and truncated day, paged if a month
returns a full page. Fallback, used only if the server rejects the truncation
function: raw created_date values restricted to the mapped types, aggregated to
days client-side. A month that fails under both strategies is halt H2.
"""

from __future__ import annotations

import csv
import json
import sys
import time
from datetime import date
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from study.categories import CATEGORIES, matches  # noqa: E402

DATA = ROOT / "data"
CACHE = DATA / "cache"
ENDPOINT = "https://data.cityofchicago.org/resource/v6vf-nfxy.json"
TIMEOUT = 120
RETRIES = 3
BACKOFF = 10
PAGE = 50000
WINDOW_START = date(2019, 1, 1)

NOT_DUP = "(duplicate IS NULL OR duplicate = false)"
NOT_LEGACY = "(legacy_record IS NULL OR legacy_record = false)"


class Rejected(Exception):
    """The server refused the query outright (4xx) rather than failing."""


def months(start: date, end: date) -> list[tuple[date, date]]:
    out = []
    y, m = start.year, start.month
    while date(y, m, 1) <= end:
        nxt = date(y + (m == 12), 1 if m == 12 else m + 1, 1)
        out.append((date(y, m, 1), nxt))
        y, m = nxt.year, nxt.month
    return out


def get(params: dict) -> list[dict]:
    last = None
    for attempt in range(1, RETRIES + 1):
        try:
            r = requests.get(ENDPOINT, params=params, timeout=TIMEOUT)
            if r.status_code == 200:
                return r.json()
            last = f"HTTP {r.status_code}: {r.text[:500]}"
            if 400 <= r.status_code < 500:
                raise Rejected(f"{r.url}\n{last}")
        except requests.RequestException as exc:
            last = f"{type(exc).__name__}: {exc}"
        print(f"    attempt {attempt}: {last}", file=sys.stderr)
        if attempt < RETRIES:
            time.sleep(BACKOFF)
    raise RuntimeError(last or "unknown failure")


def where(a: date, b: date, extra: str = "") -> str:
    w = (f"created_date >= '{a.isoformat()}T00:00:00'"
         f" AND created_date < '{b.isoformat()}T00:00:00'"
         f" AND {NOT_DUP} AND {NOT_LEGACY}")
    return w + extra


def primary_month(a: date, b: date) -> tuple[list[tuple[str, str, int]], int]:
    """Grouped counts for one month. Returns (rows, pages_used)."""
    rows: list[tuple[str, str, int]] = []
    offset, pages = 0, 0
    while True:
        chunk = get({
            "$select": "sr_type,date_trunc_ymd(created_date) AS day,count(*) AS n",
            "$where": where(a, b),
            "$group": "sr_type,date_trunc_ymd(created_date)",
            "$limit": PAGE,
            "$offset": offset,
        })
        pages += 1
        for r in chunk:
            rows.append((r["day"][:10], r["sr_type"], int(r["n"])))
        if len(chunk) < PAGE:
            return rows, pages
        offset += PAGE


def fallback_month(a: date, b: date, wanted: list[str]) -> tuple[list, int]:
    """Raw created_date for the mapped types only, aggregated client-side."""
    quoted = ",".join("'" + s.replace("'", "''") + "'" for s in wanted)
    agg: dict[tuple[str, str], int] = {}
    offset, pages = 0, 0
    while True:
        chunk = get({
            "$select": "sr_type,created_date",
            "$where": where(a, b, f" AND sr_type IN ({quoted})"),
            "$limit": PAGE,
            "$offset": offset,
        })
        pages += 1
        for r in chunk:
            key = (r["created_date"][:10], r["sr_type"])
            agg[key] = agg.get(key, 0) + 1
        if len(chunk) < PAGE:
            break
        offset += PAGE
    return [(d, s, n) for (d, s), n in agg.items()], pages


def main() -> int:
    with (DATA / "weather_daily.csv").open(encoding="utf-8") as fh:
        wdays = [r["day"] for r in csv.DictReader(fh)]
    end = date(*(int(x) for x in wdays[-1].split("-")))
    print(f"window {wdays[0]} .. {wdays[-1]}")

    with (DATA / "sr_types.csv").open(encoding="utf-8") as fh:
        sr_types = [r["sr_type"] for r in csv.DictReader(fh)]
    wanted = sorted({s for c in CATEGORIES for s in matches(c["keyword"], sr_types)})

    CACHE.mkdir(parents=True, exist_ok=True)
    all_rows: list[tuple[str, str, int]] = []
    notes = {"paged_months": [], "fallback_months": [], "empty_months": []}

    for a, b in months(WINDOW_START, end):
        tag = f"{a.year}-{a.month:02d}"
        cached = CACHE / f"311_{tag}.json"
        if cached.exists():
            payload = json.loads(cached.read_text(encoding="utf-8"))
            all_rows.extend(tuple(r) for r in payload["rows"])
            if payload["strategy"] == "fallback":
                notes["fallback_months"].append(tag)
            if payload["pages"] > 1:
                notes["paged_months"].append(tag)
            print(f"  {tag}: {len(payload['rows'])} rows (cached)")
            continue

        strategy = "primary"
        try:
            rows, pages = primary_month(a, b)
        except (Rejected, RuntimeError) as exc:
            print(f"  {tag}: primary failed: {exc}", file=sys.stderr)
            strategy = "fallback"
            try:
                rows, pages = fallback_month(a, b, wanted)
            except (Rejected, RuntimeError) as exc2:
                print(f"H2: month {tag} failed under both strategies.",
                      file=sys.stderr)
                print(f"  {exc2}", file=sys.stderr)
                return 2
            notes["fallback_months"].append(tag)

        if pages > 1:
            notes["paged_months"].append(tag)
        if not rows:
            notes["empty_months"].append(tag)
        cached.write_text(
            json.dumps({"strategy": strategy, "pages": pages, "rows": rows}),
            encoding="utf-8",
        )
        all_rows.extend(rows)
        print(f"  {tag}: {len(rows)} rows, {pages} page(s), {strategy}")
        time.sleep(0.5)

    all_rows.sort()
    out = DATA / "311_daily_by_type.csv"
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["day", "sr_type", "n"])
        w.writerows(all_rows)

    (DATA / "pull_notes.json").write_text(json.dumps(notes, indent=2),
                                          encoding="utf-8")
    print(f"wrote {out}: {len(all_rows)} rows")
    print(f"paged months: {notes['paged_months'] or 'none'}")
    print(f"fallback months: {notes['fallback_months'] or 'none'}")
    print(f"empty months: {notes['empty_months'] or 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
