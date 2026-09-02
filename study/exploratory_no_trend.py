"""Exploratory variant: the same study with the trend covariate removed.

Designed after the registered results were seen. It re-scores nothing. The
registered verdicts in results/results.md stand; this run exists to show how
much they depend on a design choice that was made in advance.

The floor here is the training mean, which cannot extrapolate and therefore
cannot carry the end of the training period across the test year. Features,
hyperparameters, split, categories, target and bootstrap are imported from the
registered modules; nothing is reimplemented.

Also writes results/trend_diagnostic.json: what the registered TREND model
actually predicts on the test year, per category.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import sklearn

from study.categories import CATEGORIES, CATEGORY_NAMES
from study.features import (
    CLOCK_COLS,
    WEATHER_COLS,
    build_features,
    load_daily,
    seasonal_naive,
    split,
    target,
)
from study.models import STAGES, make_model, run_category
from study.score import UNDEFINED, bootstrap, recovery, skills, verdicts

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"

BASE = "MEAN"
MODEL_NAMES = [BASE, "WEATHER", "CLOCK", "BOTH"]
FEATURE_SETS = {
    "WEATHER": list(WEATHER_COLS),
    "CLOCK": list(CLOCK_COLS),
    "BOTH": list(WEATHER_COLS) + list(CLOCK_COLS),
}
ROLE = {c["name"]: c["role"] for c in CATEGORIES}


def fmt(x, nd=4):
    if x is None:
        return "UNDEFINED"
    if isinstance(x, str):
        return x
    return f"{x:.{nd}f}"


def run_category_no_trend(feat, y, train: np.ndarray, test: np.ndarray,
                          staged: bool = False) -> dict:
    """Fit the three feature-set models plus the constant floor.

    MEAN has no features at all: it predicts the mean of the training targets,
    which is what a model with nothing to split on would return.
    """
    y_arr = np.asarray(y, dtype="float64")
    y_train = y_arr[train]
    y_test = y_arr[test]

    preds: dict[str, np.ndarray] = {
        BASE: np.full(int(test.sum()), float(y_train.mean()), dtype="float64")
    }
    staged_preds: dict[str, np.ndarray] = {}

    for name in ["WEATHER", "CLOCK", "BOTH"]:
        cols = FEATURE_SETS[name]
        X = feat[cols].to_numpy(dtype="float64")
        model = make_model()
        model.fit(X[train], y_train)
        preds[name] = model.predict(X[test])
        if staged and name == "WEATHER":
            all_stages = list(model.staged_predict(X[test]))
            staged_preds[name] = np.array(
                [all_stages[s - 1] for s in STAGES], dtype="float64"
            )

    mae = {m: float(np.mean(np.abs(p - y_test))) for m, p in preds.items()}
    return {"y_test": y_test, "preds": preds, "mae": mae, "staged": staged_preds}


def trend_diagnostic(feat, train, test, days) -> dict:
    """What the registered TREND model predicts across the test year.

    Every test day has a larger t than any training day, so a tree ensemble
    returns its last leaf for all of them.
    """
    out = {}
    for cat in CATEGORY_NAMES:
        y = target(feat, cat)
        res = run_category(feat, y, train, test)
        p = res["preds"]["TREND"]
        uniq = np.unique(np.round(p, 6))
        naive = seasonal_naive(feat, y, train, test)
        counts = np.expm1(res["y_test"])
        out[cat] = {
            "trend_distinct_predictions_on_test": int(uniq.size),
            "trend_constant_log1p": float(uniq[0]) if uniq.size == 1 else None,
            "trend_implied_counts_per_day": (
                float(np.expm1(uniq[0])) if uniq.size == 1 else None),
            "test_median_count_per_day": float(np.median(counts)),
            "mae_trend": float(res["mae"]["TREND"]),
            "mae_seasonal_naive": float(np.mean(np.abs(naive - res["y_test"]))),
        }
        out[cat]["trend_mae_over_naive_mae"] = (
            out[cat]["mae_trend"] / out[cat]["mae_seasonal_naive"])
    return out


def main() -> int:
    daily = load_daily()
    feat = build_features(daily)
    train, test = split(feat)
    days = feat["day"]

    month_key = days.dt.strftime("%Y-%m").to_numpy()
    test_months = sorted(set(month_key[test]))
    month_index = np.array(
        [test_months.index(m) for m in month_key[test]], dtype="int64"
    )

    registered = json.loads(
        (RESULTS / "results.json").read_text(encoding="utf-8"))

    per_category: dict[str, dict] = {}
    frames = {"stages": STAGES, "months": test_months, "categories": {}}

    for cat in CATEGORY_NAMES:
        y = target(feat, cat)
        res = run_category_no_trend(feat, y, train, test, staged=True)
        mae = res["mae"]
        sk = skills(mae, base=BASE)
        rec = recovery(sk)
        boot = bootstrap(res["y_test"], res["preds"], month_index, base=BASE)

        per_category[cat] = {
            "role": ROLE[cat],
            "mae": mae,
            "skill": sk,
            "recovery": rec,
            "bootstrap": boot,
        }

        actual_counts = daily.set_index("day").loc[
            days[test].to_numpy(), cat
        ].to_numpy(dtype="float64")
        actual_by_month = [
            float(actual_counts[month_index == i].sum())
            for i in range(len(test_months))
        ]
        model_by_month = []
        for row in res["staged"]["WEATHER"]:
            counts = np.clip(np.expm1(row), 0.0, None)
            model_by_month.append([
                float(counts[month_index == i].sum())
                for i in range(len(test_months))
            ])
        frames["categories"][cat] = {
            "actual": actual_by_month,
            "model": model_by_month,
        }

        print(f"{cat}: MAE " + "  ".join(f"{m}={mae[m]:.4f}"
                                         for m in MODEL_NAMES))
        print("  skill " + "  ".join(f"{m}={sk[m]:+.4f}"
                                     for m in MODEL_NAMES[1:])
              + f"   recovery={fmt(rec)}")

    would = verdicts(per_category)
    diag = trend_diagnostic(feat, train, test, days)

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "exploratory_no_trend.json").write_text(
        json.dumps({
            "meta": {
                "designed": "after the registered results were seen",
                "floor": "training mean of the target",
                "sklearn_version": sklearn.__version__,
                "test_months": test_months,
            },
            "categories": per_category,
            "would_have_been": would,
        }, indent=2),
        encoding="utf-8",
    )
    (RESULTS / "exploratory_frames.json").write_text(
        json.dumps(frames), encoding="utf-8")
    (RESULTS / "trend_diagnostic.json").write_text(
        json.dumps(diag, indent=2), encoding="utf-8")

    lines = [
        "# Exploratory results — trend covariate removed",
        "",
        "Exploratory. This analysis was designed after the registered results "
        "were seen. It removes the trend covariate from every model. It does "
        "not re-score any prediction; the registered verdicts in results.md "
        "stand. It is reported because the registered design carries a defect "
        "described in DISCUSSION.md, and because the comparison shows how much "
        "the verdicts depend on a design choice made in advance.",
        "",
        "The floor model here is MEAN: the mean of the training targets, "
        "predicted for every test day. Skill is 1 - MAE/MAE(MEAN). WEATHER "
        "carries the weather block alone, CLOCK the clock block alone, BOTH "
        "the union. Hyperparameters, split, categories, target and bootstrap "
        "are unchanged.",
        "",
    ]

    for cat in CATEGORY_NAMES:
        d = per_category[cat]
        b = d["bootstrap"]
        lines += [
            f"## {cat} ({d['role']})",
            "",
            "| Model | MAE | MAE 90% interval | Skill | Skill 90% interval |",
            "|---|---|---|---|---|",
        ]
        for m in MODEL_NAMES:
            mb = b[f"mae_{m}"]
            if m == BASE:
                sk_cell, sk_int = "-", "-"
            else:
                sb = b[f"skill_{m}"]
                sk_cell = fmt(d["skill"][m])
                sk_int = f"{fmt(sb['p5'])} to {fmt(sb['p95'])}"
            lines.append(
                f"| {m} | {fmt(d['mae'][m])} | "
                f"{fmt(mb['p5'])} to {fmt(mb['p95'])} | {sk_cell} | {sk_int} |"
            )
        rb = b["recovery"]
        if isinstance(d["recovery"], str):
            rec_line = (f"Recovery: {UNDEFINED} (skill(CLOCK) = "
                        f"{fmt(d['skill']['CLOCK'])} is not above 0.05).")
        else:
            rec_line = (f"Recovery: {fmt(d['recovery'])} "
                        f"(90% interval {fmt(rb['p5'])} to {fmt(rb['p95'])}; "
                        f"{rb['draws_defined']} of {b['draws']} resamples "
                        f"defined).")
        lines += ["", rec_line, ""]

    lines += [
        "## Side by side with the registered analysis",
        "",
        "The registered column is read from results/results.json and is the "
        "scored result. The exploratory column is this run. The last column is "
        "the word the exploratory value would have produced had it been put "
        "through the registered threshold; it is not a verdict, and no verdict "
        "changes.",
        "",
        "| Code | Category | Prediction | Registered observed | Verdict | "
        "Exploratory observed | Would have been |",
        "|---|---|---|---|---|---|---|",
    ]
    reg_by_code = {v["code"]: v for v in registered["verdicts"]}
    for w in would:
        r = reg_by_code[w["code"]]
        lines.append(
            f"| {w['code']} | {w['category']} | {w['prediction']} | "
            f"{r['observed']} | {r['verdict']} | {w['observed']} | "
            f"{w['verdict']} |"
        )
    lines += [
        "",
        "The two exploratory categories, tree debris and abandoned vehicle, "
        "carry no prediction in either analysis.",
        "",
    ]

    (RESULTS / "exploratory_no_trend.md").write_text(
        "\n".join(lines), encoding="utf-8")

    print()
    for w in would:
        r = reg_by_code[w["code"]]
        print(f"{w['code']} {w['category']}: registered {r['verdict']} "
              f"({r['observed']}) | exploratory would have been "
              f"{w['verdict']} ({w['observed']})")
    print()
    for cat, d in diag.items():
        print(f"TREND on {cat}: {d['trend_distinct_predictions_on_test']} "
              f"distinct prediction(s), constant "
              f"{fmt(d['trend_constant_log1p'])} "
              f"(~{d['trend_implied_counts_per_day']:.1f}/day), test median "
              f"{d['test_median_count_per_day']:.0f}/day, "
              f"MAE {d['mae_trend']:.4f} vs naive "
              f"{d['mae_seasonal_naive']:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
