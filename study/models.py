"""The four models, their feature sets, and the single fitting path.

run_category is the only place a model is fitted. The positive controls in
tests/test_study.py call it with synthetic or permuted targets; the study calls
it with the real ones. There is no second code path.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

from study.features import CLOCK_COLS, TREND_COLS, WEATHER_COLS

HPARAMS = dict(
    max_iter=300,
    learning_rate=0.05,
    max_leaf_nodes=15,
    min_samples_leaf=20,
    l2_regularization=1.0,
    early_stopping=False,
    random_state=0,
)

FEATURE_SETS: dict[str, list[str]] = {
    "TREND": list(TREND_COLS),
    "WEATHER": list(TREND_COLS) + list(WEATHER_COLS),
    "CLOCK": list(TREND_COLS) + list(CLOCK_COLS),
    "BOTH": list(TREND_COLS) + list(WEATHER_COLS) + list(CLOCK_COLS),
}
MODEL_NAMES = ["TREND", "WEATHER", "CLOCK", "BOTH"]

STAGES = [1, 2, 3, 5, 8, 13, 20, 30, 50, 80, 120, 200, 300]


def make_model() -> HistGradientBoostingRegressor:
    return HistGradientBoostingRegressor(**HPARAMS)


def run_category(feat: pd.DataFrame, y, train: np.ndarray, test: np.ndarray,
                 shuffle_train: bool = False, shuffle_seed: int = 0,
                 staged: bool = False) -> dict:
    """Fit all four models on the training rows and predict the test rows.

    Returns per-model test predictions and MAEs on the target's own scale.
    With shuffle_train, the training targets are permuted before fitting and
    the test targets are left alone.
    """
    y_arr = np.asarray(y, dtype="float64")
    y_train = y_arr[train]
    if shuffle_train:
        y_train = np.random.default_rng(shuffle_seed).permutation(y_train)
    y_test = y_arr[test]

    preds: dict[str, np.ndarray] = {}
    maes: dict[str, float] = {}
    staged_preds: dict[str, np.ndarray] = {}

    for name in MODEL_NAMES:
        cols = FEATURE_SETS[name]
        X = feat[cols].to_numpy(dtype="float64")
        model = make_model()
        model.fit(X[train], y_train)
        p = model.predict(X[test])
        preds[name] = p
        maes[name] = float(np.mean(np.abs(p - y_test)))
        if staged and name == "WEATHER":
            all_stages = list(model.staged_predict(X[test]))
            staged_preds[name] = np.array(
                [all_stages[s - 1] for s in STAGES], dtype="float64"
            )

    return {
        "y_test": y_test,
        "preds": preds,
        "mae": maes,
        "staged": staged_preds,
    }
