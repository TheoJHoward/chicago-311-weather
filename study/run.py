"""Run the study and write results/.

Outputs:
  results/results.json  every MAE, skill, recovery, bootstrap interval, verdict
  results/results.md    one table per category, then the P1-P4 verdict table
  results/frames.json   the WEATHER model's monthly predictions by tree count
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import sklearn

from study.categories import CATEGORIES, CATEGORY_NAMES
from study.features import (
    build_features,
    load_daily,
    seasonal_naive,
    split,
    target,
)
from study.models import MODEL_NAMES, STAGES, run_category
from study.score import UNDEFINED, bootstrap, recovery, skills, verdicts

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"

ROLE = {c["name"]: c["role"] for c in CATEGORIES}


def fmt(x, nd=4):
    if isinstance(x, str) or x is None:
        return "UNDEFINED" if x is None else x
    return f"{x:.{nd}f}"


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

    meta = {
        "data_window_start": str(daily["day"].iloc[0].date()),
        "data_window_end": str(daily["day"].iloc[-1].date()),
        "data_window_days": int(len(daily)),
        "modelled_first_day": str(days.iloc[0].date()),
        "modelled_last_day": str(days.iloc[-1].date()),
        "rows_after_warmup_drop": int(len(feat)),
        "training_days": int(train.sum()),
        "training_first_day": str(days[train].iloc[0].date()),
        "training_last_day": str(days[train].iloc[-1].date()),
        "test_days": int(test.sum()),
        "test_first_day": str(days[test].iloc[0].date()),
        "test_last_day": str(days[test].iloc[-1].date()),
        "test_months": test_months,
        "sklearn_version": sklearn.__version__,
        "bootstrap_stages": STAGES,
    }

    per_category: dict[str, dict] = {}
    frames = {"stages": STAGES, "months": test_months, "categories": {}}

    for cat in CATEGORY_NAMES:
        y = target(feat, cat)
        res = run_category(feat, y, train, test, staged=True)
        mae = res["mae"]
        sk = skills(mae)
        rec = recovery(sk)

        naive_pred = seasonal_naive(feat, y, train, test)
        naive_mae = float(np.mean(np.abs(naive_pred - res["y_test"])))
        naive_skill = 1.0 - naive_mae / mae["TREND"]

        boot = bootstrap(res["y_test"], res["preds"], month_index)

        per_category[cat] = {
            "role": ROLE[cat],
            "mae": mae,
            "skill": sk,
            "recovery": rec,
            "seasonal_naive": {"mae": naive_mae, "skill": naive_skill},
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

        print(f"{cat}: MAE " + "  ".join(f"{m}={mae[m]:.4f}" for m in MODEL_NAMES))
        print(f"  skill " + "  ".join(f"{m}={sk[m]:+.4f}"
                                      for m in MODEL_NAMES[1:])
              + f"   recovery={fmt(rec)}")

    v = verdicts(per_category)

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "results.json").write_text(
        json.dumps({"meta": meta, "categories": per_category,
                    "verdicts": v}, indent=2),
        encoding="utf-8",
    )
    (RESULTS / "frames.json").write_text(json.dumps(frames), encoding="utf-8")

    lines = [
        "# Results",
        "",
        f"Data window {meta['data_window_start']} through "
        f"{meta['data_window_end']} ({meta['data_window_days']} days). The "
        f"first seven days are dropped because their lags reach before the "
        f"window start, so the modelled days run "
        f"{meta['modelled_first_day']} through {meta['modelled_last_day']}. "
        f"Training days {meta['training_first_day']} through "
        f"{meta['training_last_day']} ({meta['training_days']} days). "
        f"Test days {meta['test_first_day']} through "
        f"{meta['test_last_day']} ({meta['test_days']} days).",
        "",
        "All errors are mean absolute error of log(1 + count) on the test set. "
        "Skill is 1 - MAE/MAE(TREND). Intervals are 5th-95th percentiles of "
        f"{per_category[CATEGORY_NAMES[0]]['bootstrap']['draws']} "
        "monthly-block bootstrap resamples of the test year; verdicts use the "
        "point estimates.",
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
            if m == "TREND":
                sk_cell, sk_int = "-", "-"
            else:
                sb = b[f"skill_{m}"]
                sk_cell = fmt(d["skill"][m])
                sk_int = f"{fmt(sb['p5'])} to {fmt(sb['p95'])}"
            lines.append(
                f"| {m} | {fmt(d['mae'][m])} | "
                f"{fmt(mb['p5'])} to {fmt(mb['p95'])} | {sk_cell} | {sk_int} |"
            )
        lines.append(
            f"| seasonal-naive (context only) | "
            f"{fmt(d['seasonal_naive']['mae'])} | - | "
            f"{fmt(d['seasonal_naive']['skill'])} | - |"
        )
        rb = b["recovery"]
        if isinstance(d["recovery"], str):
            rec_line = (f"Recovery: {UNDEFINED} "
                        f"(skill(CLOCK) = {fmt(d['skill']['CLOCK'])} is not "
                        f"above 0.05).")
        else:
            rec_line = (f"Recovery: {fmt(d['recovery'])} "
                        f"(90% interval {fmt(rb['p5'])} to {fmt(rb['p95'])}; "
                        f"{rb['draws_defined']} of {b['draws']} resamples "
                        f"defined).")
        lines += ["", rec_line, ""]

    lines += [
        "## Verdicts",
        "",
        "| Code | Category | Prediction | Observed | Verdict |",
        "|---|---|---|---|---|",
    ]
    for r in v:
        lines.append(
            f"| {r['code']} | {r['category']} | {r['prediction']} | "
            f"{r['observed']} | {r['verdict']} |"
        )
    lines += [
        "",
        "The two exploratory categories, tree debris and abandoned vehicle, "
        "carry no prediction and appear above for reporting only.",
        "",
    ]

    (RESULTS / "results.md").write_text("\n".join(lines), encoding="utf-8")
    print()
    for r in v:
        print(f"{r['code']} {r['category']}: {r['verdict']} ({r['observed']})")
    print(f"\nwrote {RESULTS / 'results.json'}, {RESULTS / 'results.md'}, "
          f"{RESULTS / 'frames.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
