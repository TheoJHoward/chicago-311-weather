"""Feature construction and the train/test split.

Every lagged or windowed feature uses only days strictly before the day being
predicted. Rows whose lags reach back before the window start are dropped, not
filled.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from study.categories import CATEGORY_NAMES

ROOT = Path(__file__).resolve().parents[1]
DAILY_CSV = ROOT / "data" / "study_daily.csv"

WEATHER_VARS = [
    "temperature_2m_max",
    "temperature_2m_min",
    "temperature_2m_mean",
    "precipitation_sum",
    "rain_sum",
    "snowfall_sum",
    "wind_speed_10m_max",
]
LAGS = [1, 2, 3]
SUM7_VARS = ["precipitation_sum", "rain_sum", "snowfall_sum"]

WINDOW_START = pd.Timestamp("2019-01-01")
TEST_DAYS = 365

# Rows before this index cannot carry a full seven-day lookback.
WARMUP_ROWS = 7

TREND_COLS = ["t"]
WEATHER_COLS = (
    WEATHER_VARS
    + [f"{v}_lag{k}" for v in WEATHER_VARS for k in LAGS]
    + [f"{v}_7d" for v in SUM7_VARS]
    + ["freeze_thaw", "freeze_thaw_7d"]
)
CLOCK_COLS = ["doy_sin", "doy_cos"] + [f"dow_{i}" for i in range(7)]


def load_daily(path: Path | str = DAILY_CSV) -> pd.DataFrame:
    """The joined daily table: one contiguous row per day, no gaps."""
    df = pd.read_csv(path, parse_dates=["day"])
    df = df.sort_values("day").reset_index(drop=True)
    gaps = df["day"].diff().dropna().unique()
    assert list(gaps) == [pd.Timedelta(days=1)], f"non-contiguous days: {gaps}"
    return df


def build_features(daily: pd.DataFrame) -> pd.DataFrame:
    """Add every feature column. Returns the frame with warm-up rows dropped."""
    f = daily.copy()
    f["t"] = (f["day"] - WINDOW_START).dt.days.astype("int64")

    for v in WEATHER_VARS:
        for k in LAGS:
            f[f"{v}_lag{k}"] = f[v].shift(k)

    # rolling(7) at day d covers d-6..d; shifting by one day gives d-7..d-1.
    for v in SUM7_VARS:
        f[f"{v}_7d"] = f[v].rolling(7).sum().shift(1)

    f["freeze_thaw"] = (
        (f["temperature_2m_min"] < 0) & (f["temperature_2m_max"] > 0)
    ).astype("int64")
    f["freeze_thaw_7d"] = f["freeze_thaw"].rolling(7).sum().shift(1)

    doy = f["day"].dt.dayofyear.astype("float64")
    f["doy_sin"] = np.sin(2 * np.pi * doy / 365.25)
    f["doy_cos"] = np.cos(2 * np.pi * doy / 365.25)
    dow = f["day"].dt.dayofweek
    for i in range(7):
        f[f"dow_{i}"] = (dow == i).astype("int64")

    f = f.iloc[WARMUP_ROWS:].reset_index(drop=True)
    cols = TREND_COLS + WEATHER_COLS + CLOCK_COLS
    assert not f[cols].isna().any().any(), "NaN survived the warm-up drop"
    return f


def split(feat: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Boolean masks. Test is the final TEST_DAYS rows; training is the rest."""
    n = len(feat)
    assert n > TEST_DAYS, "window shorter than the test set"
    test = np.zeros(n, dtype=bool)
    test[-TEST_DAYS:] = True
    return ~test, test


def target(daily_or_feat: pd.DataFrame, category: str) -> pd.Series:
    """log(1 + count) for one category."""
    assert category in CATEGORY_NAMES, category
    return np.log1p(daily_or_feat[category].astype("float64"))


def seasonal_naive(feat: pd.DataFrame, y: pd.Series,
                   train: np.ndarray, test: np.ndarray,
                   half_width: int = 3) -> np.ndarray:
    """Mean training target over training days within +/- half_width days of
    the same day-of-year. Training days only; the test period is never read."""
    doy = feat["day"].dt.dayofyear.to_numpy()
    y_arr = np.asarray(y, dtype="float64")
    train_doy = doy[train]
    train_y = y_arr[train]
    grand = float(train_y.mean())

    out = np.empty(int(test.sum()), dtype="float64")
    for j, d in enumerate(doy[test]):
        # circular distance on a 366-day ring
        diff = np.abs(train_doy - d)
        diff = np.minimum(diff, 366 - diff)
        sel = train_y[diff <= half_width]
        out[j] = float(sel.mean()) if sel.size else grand
    return out
