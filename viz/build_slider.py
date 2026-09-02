"""Precompute the slider toy's prediction grid.

For each category, the WEATHER model is fitted on the training rows with the
registered hyperparameters and the registered WEATHER feature set, then asked
for a prediction at every point of a coarse grid over maximum temperature,
precipitation and snowfall. Every other input is held at a stated constant.

This is a toy: the grid points are not real days, and the constants below are
simplifications. They are listed on the page itself.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from study.categories import CATEGORY_NAMES  # noqa: E402
from study.features import (  # noqa: E402
    LAGS,
    SUM7_VARS,
    WEATHER_VARS,
    build_features,
    load_daily,
    split,
    target,
)
from study.models import FEATURE_SETS, make_model  # noqa: E402

TMAX = list(range(-25, 41))
PRECIP = [0.0, 2.0, 10.0, 25.0]
SNOW = [0.0, 5.0]
TMIN_OFFSET = -8.0


def grid_row(tmax: float, precip: float, snow: float,
             wind: float, t: float) -> dict:
    tmin = tmax + TMIN_OFFSET
    same = {
        "temperature_2m_max": tmax,
        "temperature_2m_min": tmin,
        "temperature_2m_mean": (tmax + tmin) / 2.0,
        "precipitation_sum": precip,
        "rain_sum": precip,
        "snowfall_sum": snow,
        "wind_speed_10m_max": wind,
    }
    row = {"t": t}
    row.update(same)
    for v in WEATHER_VARS:
        for k in LAGS:
            row[f"{v}_lag{k}"] = same[v]
    for v in SUM7_VARS:
        row[f"{v}_7d"] = 7.0 * same[v]
    ft = 1.0 if (tmin < 0 and tmax > 0) else 0.0
    row["freeze_thaw"] = ft
    row["freeze_thaw_7d"] = 7.0 * ft
    return row


def main() -> int:
    daily = load_daily()
    feat = build_features(daily)
    train, test = split(feat)

    cols = FEATURE_SETS["WEATHER"]
    wind = float(np.median(feat.loc[train, "wind_speed_10m_max"]))
    t_last = float(feat.loc[train, "t"].max())

    rows = []
    index = []
    for si, snow in enumerate(SNOW):
        for pi, precip in enumerate(PRECIP):
            for ti, tmax in enumerate(TMAX):
                rows.append(grid_row(float(tmax), precip, snow, wind, t_last))
                index.append((si, pi, ti))
    X = np.array([[r[c] for c in cols] for r in rows], dtype="float64")

    values = {}
    for cat in CATEGORY_NAMES:
        model = make_model()
        model.fit(feat.loc[train, cols].to_numpy(dtype="float64"),
                  np.asarray(target(feat, cat))[train])
        pred = np.clip(np.expm1(model.predict(X)), 0.0, None)
        cube = [[[0.0] * len(TMAX) for _ in PRECIP] for _ in SNOW]
        for (si, pi, ti), v in zip(index, pred):
            cube[si][pi][ti] = round(float(v), 2)
        values[cat] = cube
        print(f"  {cat}: fitted, grid {len(pred)} points")

    payload = {
        "tmax": TMAX,
        "precip": PRECIP,
        "snow": SNOW,
        "wind": round(wind, 2),
        "t_last_training_day": str(feat.loc[train, "day"].max().date()),
        "t_value": t_last,
        "categories": values,
    }
    out = ROOT / "results" / "slider_grid.json"
    out.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size} bytes); "
          f"wind held at {wind:.2f}, t held at {t_last:.0f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
