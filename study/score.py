"""Metrics, bootstrap intervals, and the verdicts.

Every threshold used here comes from study.prereg_thresholds, which mirrors
PREREG.md. Nothing in this module is re-scored or adjusted after the fact.
"""

from __future__ import annotations

import numpy as np

from study.prereg_thresholds import (
    BOOTSTRAP_DRAWS,
    BOOTSTRAP_HI,
    BOOTSTRAP_LO,
    BOOTSTRAP_SEED,
    CLOCK_SKILL_DEFINED_MIN,
    P4_WEATHER_SKILL_MAX,
    RECOVERY_HELD_MIN,
    RECOVERY_LOW_MAX,
)

UNDEFINED = "UNDEFINED"


def skills(mae: dict[str, float]) -> dict[str, float]:
    base = mae["TREND"]
    return {m: 1.0 - v / base for m, v in mae.items()}


def recovery(skill: dict[str, float]):
    """skill(WEATHER)/skill(CLOCK), or UNDEFINED when skill(CLOCK) is too small."""
    if skill["CLOCK"] > CLOCK_SKILL_DEFINED_MIN:
        return skill["WEATHER"] / skill["CLOCK"]
    return UNDEFINED


def bootstrap(y_test: np.ndarray, preds: dict[str, np.ndarray],
              month_index: np.ndarray) -> dict:
    """Monthly-block resampling of the test year.

    Draws twelve months with replacement, concatenates their days, and
    recomputes MAE, skill and recovery on the resampled days.
    """
    months = np.unique(month_index)
    blocks = [np.flatnonzero(month_index == m) for m in months]
    abs_err = {m: np.abs(p - y_test) for m, p in preds.items()}

    rng = np.random.default_rng(BOOTSTRAP_SEED)
    draws: dict[str, list[float]] = {k: [] for k in
                                     ["mae_TREND", "mae_WEATHER", "mae_CLOCK",
                                      "mae_BOTH", "skill_WEATHER",
                                      "skill_CLOCK", "skill_BOTH"]}
    rec_draws: list[float] = []
    rec_undefined = 0

    for _ in range(BOOTSTRAP_DRAWS):
        pick = rng.integers(0, len(blocks), size=len(blocks))
        idx = np.concatenate([blocks[i] for i in pick])
        mae = {m: float(abs_err[m][idx].mean()) for m in abs_err}
        sk = skills(mae)
        for m in ["TREND", "WEATHER", "CLOCK", "BOTH"]:
            draws[f"mae_{m}"].append(mae[m])
        for m in ["WEATHER", "CLOCK", "BOTH"]:
            draws[f"skill_{m}"].append(sk[m])
        r = recovery(sk)
        if r is UNDEFINED or r == UNDEFINED:
            rec_undefined += 1
        else:
            rec_draws.append(r)

    out = {
        k: {
            "p5": float(np.percentile(v, BOOTSTRAP_LO)),
            "p95": float(np.percentile(v, BOOTSTRAP_HI)),
        }
        for k, v in draws.items()
    }
    out["recovery"] = {
        "p5": float(np.percentile(rec_draws, BOOTSTRAP_LO)) if rec_draws else None,
        "p95": float(np.percentile(rec_draws, BOOTSTRAP_HI)) if rec_draws else None,
        "draws_defined": len(rec_draws),
        "draws_undefined": rec_undefined,
    }
    out["draws"] = BOOTSTRAP_DRAWS
    return out


def _is_defined(rec) -> bool:
    return not isinstance(rec, str)


def verdicts(per_category: dict) -> list[dict]:
    """Score P1-P4 from the point estimates.

    P1 and P2 name a numeric floor for recovery, so a recovery that is
    UNDEFINED does not meet them and is scored MISSED. P4 names UNDEFINED
    explicitly as one of its two ways to hold.
    """
    out = []

    for code, cat in (("P1", "pothole"), ("P2", "rodent")):
        rec = per_category[cat]["recovery"]
        held = _is_defined(rec) and rec >= RECOVERY_HELD_MIN
        out.append({
            "code": code,
            "category": cat,
            "prediction": f"recovery >= {RECOVERY_HELD_MIN}",
            "observed": ("recovery = UNDEFINED" if not _is_defined(rec)
                         else f"recovery = {rec:.4f}"),
            "verdict": "HELD" if held else "MISSED",
        })

    sk = per_category["basement"]["skill"]
    held = sk["WEATHER"] > sk["CLOCK"]
    out.append({
        "code": "P3",
        "category": "basement",
        "prediction": "skill(WEATHER) > skill(CLOCK)",
        "observed": (f"skill(WEATHER) = {sk['WEATHER']:.4f}, "
                     f"skill(CLOCK) = {sk['CLOCK']:.4f}"),
        "verdict": "HELD" if held else "MISSED",
    })

    g = per_category["graffiti"]
    rec, gs = g["recovery"], g["skill"]
    if _is_defined(rec):
        held = rec < RECOVERY_LOW_MAX
        observed = f"recovery = {rec:.4f}"
    else:
        held = gs["WEATHER"] < P4_WEATHER_SKILL_MAX
        observed = (f"recovery = UNDEFINED, "
                    f"skill(WEATHER) = {gs['WEATHER']:.4f}")
    out.append({
        "code": "P4",
        "category": "graffiti",
        "prediction": (f"recovery < {RECOVERY_LOW_MAX}, or UNDEFINED with "
                       f"skill(WEATHER) < {P4_WEATHER_SKILL_MAX}"),
        "observed": observed,
        "verdict": "HELD" if held else "MISSED",
    })
    return out
