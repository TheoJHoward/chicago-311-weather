"""Instrument tests and the registered positive controls.

The positive controls call the same run_category the study calls. A control
that fails stops the study; it is never adjusted toward a pass.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from study.features import (
    LAGS,
    SUM7_VARS,
    WARMUP_ROWS,
    WEATHER_VARS,
    build_features,
    load_daily,
    seasonal_naive,
    split,
    target,
)
from study.models import run_category
from study.prereg_thresholds import (
    PC3_SKILL_ABS_MAX,
    PC_SKILL_MIN,
    PREREG_STRINGS,
)
from study.score import skills

ROOT = Path(__file__).resolve().parents[1]

# The positive controls record their skills here so that any later reading of
# those numbers comes from a file the run wrote.
PC_SKILLS: dict[str, dict[str, float]] = {}

FIXED_DAYS = [
    "2019-06-15",
    "2020-11-03",
    "2022-02-14",
    "2024-07-04",
    "2025-12-25",
]


@pytest.fixture(scope="module")
def daily():
    return load_daily()


@pytest.fixture(scope="module")
def feat(daily):
    return build_features(daily)


@pytest.fixture(scope="module")
def masks(feat):
    return split(feat)


@pytest.fixture(scope="module", autouse=True)
def _record_positive_controls():
    yield
    if PC_SKILLS:
        out = ROOT / "results"
        out.mkdir(parents=True, exist_ok=True)
        (out / "positive_controls.json").write_text(
            json.dumps(PC_SKILLS, indent=2, sort_keys=True), encoding="utf-8"
        )


def test_split_no_overlap(feat, masks):
    train, test = masks
    days = feat["day"]
    assert train.sum() + test.sum() == len(feat)
    assert not (train & test).any()
    assert test.sum() == 365
    assert days[train].max() < days[test].min()
    assert days[test].min() - days[train].max() == pd.Timedelta(days=1)


def test_lag_features_prior_days(daily, feat):
    raw = daily.set_index("day")
    built = feat.set_index("day")
    ft_raw = ((raw["temperature_2m_min"] < 0)
              & (raw["temperature_2m_max"] > 0)).astype(int)

    for d in FIXED_DAYS:
        day = pd.Timestamp(d)
        assert day in built.index
        for v in WEATHER_VARS:
            for k in LAGS:
                prior = raw.loc[day - pd.Timedelta(days=k), v]
                assert built.loc[day, f"{v}_lag{k}"] == pytest.approx(prior), (
                    f"{v}_lag{k} on {d}"
                )
        for v in SUM7_VARS:
            window = [raw.loc[day - pd.Timedelta(days=k), v]
                      for k in range(1, 8)]
            assert built.loc[day, f"{v}_7d"] == pytest.approx(sum(window)), (
                f"{v}_7d on {d}"
            )
        window_ft = sum(ft_raw.loc[day - pd.Timedelta(days=k)]
                        for k in range(1, 8))
        assert built.loc[day, "freeze_thaw_7d"] == window_ft, (
            f"freeze_thaw_7d on {d}"
        )
        assert built.loc[day, "freeze_thaw"] == ft_raw.loc[day]


def test_naive_uses_train_only(feat, masks):
    train, test = masks
    y = target(feat, "pothole")
    base = seasonal_naive(feat, y, train, test)

    poisoned = y.copy()
    poisoned[test] = 999.0
    after = seasonal_naive(feat, poisoned, train, test)

    assert np.allclose(base, after)


def test_pc1_weather_synthetic(feat, masks):
    train, test = masks
    noise = np.random.default_rng(0).normal(size=len(feat))
    y = (2.0 * feat["freeze_thaw_7d"].to_numpy(dtype="float64")
         + 0.5 * feat["rain_sum_7d"].to_numpy(dtype="float64")
         + noise)
    sk = skills(run_category(feat, y, train, test)["mae"])
    PC_SKILLS["PC1_weather_driven_synthetic"] = sk
    assert sk["WEATHER"] > sk["CLOCK"], sk
    assert sk["WEATHER"] > PC_SKILL_MIN, sk


def test_pc2_clock_synthetic(feat, masks):
    train, test = masks
    noise = np.random.default_rng(0).normal(size=len(feat))
    doy = feat["day"].dt.dayofyear.to_numpy(dtype="float64")
    monday = (feat["day"].dt.dayofweek == 0).to_numpy(dtype="float64")
    y = 2.0 * np.sin(2 * np.pi * doy / 365.25) + 0.5 * monday + noise
    sk = skills(run_category(feat, y, train, test)["mae"])
    PC_SKILLS["PC2_calendar_driven_synthetic"] = sk
    assert sk["CLOCK"] > sk["WEATHER"], sk
    assert sk["CLOCK"] > PC_SKILL_MIN, sk


def test_pc3_shuffle(feat, masks):
    train, test = masks
    y = target(feat, "pothole")
    sk = skills(run_category(feat, y, train, test,
                             shuffle_train=True, shuffle_seed=0)["mae"])
    PC_SKILLS["PC3_shuffled_pothole_target"] = sk
    for m in ["WEATHER", "CLOCK", "BOTH"]:
        assert abs(sk[m]) < PC3_SKILL_ABS_MAX, (m, sk)


def test_thresholds_match_prereg():
    text = (ROOT / "PREREG.md").read_text(encoding="utf-8")
    for s in PREREG_STRINGS:
        assert s in text, s


def test_warmup_drop_is_seven_days(daily, feat):
    assert len(daily) - len(feat) == WARMUP_ROWS
    assert feat["day"].iloc[0] == daily["day"].iloc[0] + pd.Timedelta(
        days=WARMUP_ROWS
    )


def test_viz_offline():
    path = ROOT / "viz" / "year_strip.html"
    if not path.exists():
        pytest.skip("viz/year_strip.html not written yet")
    text = path.read_text(encoding="utf-8")
    for token in ["http", "src=", "@import"]:
        assert token not in text, token
