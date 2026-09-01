"""Join the 311 daily counts to the weather archive, one row per day.

Writes data/study_daily.csv (day, six category counts, seven weather columns)
and data/build_facts.json, which records what the data looked like as found:
per-type first and last appearance, per-category totals, zero-count days, and
any day in the window with no 311 record of any type.
"""

from __future__ import annotations

import csv
import json
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from study.categories import CATEGORIES, CATEGORY_NAMES, matches  # noqa: E402

DATA = ROOT / "data"
WVARS = [
    "temperature_2m_max",
    "temperature_2m_min",
    "temperature_2m_mean",
    "precipitation_sum",
    "rain_sum",
    "snowfall_sum",
    "wind_speed_10m_max",
]


def main() -> int:
    with (DATA / "weather_daily.csv").open(encoding="utf-8") as fh:
        weather = {r["day"]: r for r in csv.DictReader(fh)}
    days = sorted(weather)
    d0 = date(*(int(x) for x in days[0].split("-")))
    d1 = date(*(int(x) for x in days[-1].split("-")))
    expected = [(d0 + timedelta(i)).isoformat()
                for i in range((d1 - d0).days + 1)]
    missing = [d for d in expected if d not in weather]
    assert not missing, f"weather rows missing for {missing[:10]}"
    assert days == expected, "weather days are not a contiguous run"

    with (DATA / "sr_types.csv").open(encoding="utf-8") as fh:
        sr_types = [r["sr_type"] for r in csv.DictReader(fh)]
    cat_of: dict[str, str] = {}
    for c in CATEGORIES:
        for s in matches(c["keyword"], sr_types):
            cat_of[s] = c["name"]

    counts = {d: dict.fromkeys(CATEGORY_NAMES, 0) for d in expected}
    seen_days: set[str] = set()
    span: dict[str, list[str]] = {}
    type_total: dict[str, int] = {}
    outside = 0

    with (DATA / "311_daily_by_type.csv").open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            day, s, n = r["day"], r["sr_type"], int(r["n"])
            if day not in counts:
                outside += 1
                continue
            seen_days.add(day)
            cat = cat_of.get(s)
            if cat is None:
                continue
            counts[day][cat] += n
            type_total[s] = type_total.get(s, 0) + n
            if s in span:
                span[s][1] = max(span[s][1], day)
                span[s][0] = min(span[s][0], day)
            else:
                span[s] = [day, day]

    out = DATA / "study_daily.csv"
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["day"] + CATEGORY_NAMES + WVARS)
        for d in expected:
            w.writerow([d]
                       + [counts[d][c] for c in CATEGORY_NAMES]
                       + [weather[d][v] for v in WVARS])

    facts = {
        "window_start": expected[0],
        "window_end": expected[-1],
        "days_in_window": len(expected),
        "days_with_no_311_record_of_any_type": sorted(
            set(expected) - seen_days),
        "rows_outside_window_discarded": outside,
        "mapped_types": {
            s: {
                "category": cat_of[s],
                "first_day_in_window": span[s][0] if s in span else None,
                "last_day_in_window": span[s][1] if s in span else None,
                "count_in_window": type_total.get(s, 0),
            }
            for s in sorted(cat_of)
        },
        "categories": {},
    }
    for c in CATEGORY_NAMES:
        series = [counts[d][c] for d in expected]
        facts["categories"][c] = {
            "total_in_window": sum(series),
            "zero_count_days": sum(1 for v in series if v == 0),
            "max_day_count": max(series),
            "mean_day_count": round(sum(series) / len(series), 3),
        }

    (DATA / "build_facts.json").write_text(json.dumps(facts, indent=2),
                                           encoding="utf-8")
    print(f"wrote {out}: {len(expected)} rows")
    print(json.dumps(facts["categories"], indent=2))
    print("days with no 311 record of any type: "
          f"{facts['days_with_no_311_record_of_any_type'] or 'none'}")
    for s, m in facts["mapped_types"].items():
        print(f"  {s}: {m['first_day_in_window']} .. {m['last_day_in_window']}"
              f"  n={m['count_in_window']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
