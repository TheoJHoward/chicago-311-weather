"""Assemble the single-screen overview page from the committed results.

Every figure the page prints is computed here from a file in the repository and
embedded as data, or emitted here as markup. Nothing on the page is typed by
hand: the recoveries, the verdict chips, the basement shares, the peak day, the
registered floor, the gridline labels and the per-panel maxima are all derived
below and injected into the template.

Sources, all read-only:
  results/frames.json               actual and registered-model monthly counts
  results/exploratory_frames.json   exploratory-model monthly counts
  results/results.json              registered recoveries and verdicts
  results/trend_diagnostic.json     the registered TREND constant
  data/study_daily.csv              daily basement counts
"""

from __future__ import annotations

import csv
import html
import json
import math
import statistics
import sys
from datetime import date
from pathlib import Path

# The report below prints a typographic minus; the default Windows console
# encoding cannot represent it.
sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
DATA_PLACEHOLDER = "__OVERVIEW_JSON__"
PANELS_PLACEHOLDER = "__PANELS_HTML__"
FORBIDDEN = ["http", "src=", "@import"]

# Stack order, bottom to top, against the validated colour slots.
CATS = ["basement", "pothole", "rodent", "graffiti", "tree debris",
        "abandoned vehicle"]
HUES_LIGHT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]
HUES_DARK = ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#008300"]

PANEL_ORDER = ["pothole", "rodent", "basement", "graffiti", "tree debris",
               "abandoned vehicle"]

MONTH_ABBR = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

DAILY_FROM = "2025-07-01"
DAILY_TO = "2026-08-31"
TRAIN_ENDS = "2025-09-01"      # the split boundary; the rule is drawn here
TRAIN_LAST_DAY = "training ends · 31 Aug 2025"

# The flood strip is drawn on log1p, the scale the study scores on. These are
# the only gridlines on the page.
GRIDLINE_COUNTS = [10, 100, 1000]
H15_MIN_SEPARATION = 0.08

MINUS = "−"               # typographic minus, for negative recoveries


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def fmt_recovery(value) -> str:
    """Two decimals, with a typographic minus for negatives."""
    if isinstance(value, str):
        raise ValueError(f"recovery is {value!r}; caller must handle it")
    return f"{value:.2f}".replace("-", MINUS)


def month_labels(keys: list[str]) -> list[str]:
    out = []
    for i, mk in enumerate(keys):
        y, m = mk.split("-")
        name = MONTH_ABBR[int(m) - 1]
        out.append(f"{name} {y}" if (i == 0 or int(m) == 1) else name)
    return out


def basement_mean_share(values: list[list[float]]) -> float:
    """values[month][cat] in CATS order; basement is index 0."""
    shares = []
    for row in values:
        total = sum(row)
        shares.append(row[0] / total if total else 0.0)
    return sum(shares) / len(shares)


def stack(block: dict, pick) -> list[list[float]]:
    """[month][cat] in CATS order."""
    n = len(pick(block[CATS[0]]))
    return [[pick(block[c])[i] for c in CATS] for i in range(n)]


def panel_markup(panels: list[dict]) -> str:
    """The six panel headers as static markup.

    Emitted here rather than built by the page's script so that the two header
    lines are real nodes in the file and can be asserted without a browser.
    """
    out = []
    for p in panels:
        dot = "dot-held" if p["chipKind"] == "held" else (
            "dot-missed" if p["chipKind"] == "missed" else "dot-held")
        chip_cls = "chip chip-none" if p["chipKind"] == "none" else "chip"
        out.append(
            f'      <div class="panel" data-cat="{html.escape(p["cat"])}">\n'
            f'        <div class="p-head">\n'
            f'          <div class="p-name">'
            f'<span class="p-sw sw-{p["slot"] + 1}"></span>'
            f'<span class="p-nm">{html.escape(p["cat"])}</span></div>\n'
            f'          <span class="{chip_cls}">'
            f'<span class="dot {dot}"></span>'
            f'<span>{html.escape(p["chip"])}</span></span>\n'
            f'        </div>\n'
            f'        <div class="p-stat">{html.escape(p["stat"])}</div>\n'
            f'        <div class="p-plot">\n'
            f'          <svg viewBox="0 0 1000 100" preserveAspectRatio="none">'
            f'</svg>\n'
            f'          <div class="p-ymax">{html.escape(p["ymaxLabel"])}</div>\n'
            f'        </div>\n'
            f'      </div>'
        )
    return "\n".join(out)


def main() -> int:
    frames = load(RESULTS / "frames.json")
    expl = load(RESULTS / "exploratory_frames.json")
    results = load(RESULTS / "results.json")
    diag = load(RESULTS / "trend_diagnostic.json")

    assert frames["stages"] == expl["stages"], "stage grids differ"
    assert frames["months"] == expl["months"], "month grids differ"
    stages = frames["stages"]
    months = frames["months"]
    n_stage = len(stages)

    fc, ec = frames["categories"], expl["categories"]

    # ---- the three rows -------------------------------------------------
    actual_stack = stack(fc, lambda b: b["actual"])
    reg_stack = [stack(fc, lambda b, s=s: b["model"][s]) for s in range(n_stage)]
    exp_stack = [stack(ec, lambda b, s=s: b["model"][s]) for s in range(n_stage)]

    counts_max = max(
        [sum(r) for r in actual_stack]
        + [sum(r) for s in reg_stack for r in s]
        + [sum(r) for s in exp_stack for r in s]
    )

    def share_label(v: float) -> str:
        """One decimal below ten, none above."""
        p = v * 100
        return f"{p:.1f}" if p < 10 else str(round(p))

    shares = {
        "actual": basement_mean_share(actual_stack),
        "registered": [basement_mean_share(s) for s in reg_stack],
        "exploratory": [basement_mean_share(s) for s in exp_stack],
    }
    # The page prints these strings verbatim; it does no formatting of its own,
    # so every numeral on screen is one this script computed.
    shares["labels"] = {
        "actual": share_label(shares["actual"]),
        "registered": [share_label(v) for v in shares["registered"]],
        "exploratory": [share_label(v) for v in shares["exploratory"]],
    }

    # ---- the six panels -------------------------------------------------
    verdict_by_cat = {v["category"]: (v["code"], v["verdict"])
                      for v in results["verdicts"]}
    panels = []
    for cat in PANEL_ORDER:
        act = fc[cat]["actual"]
        reg = fc[cat]["model"]
        exp = ec[cat]["model"]
        ymax = max(max(act), max(max(r) for r in reg), max(max(r) for r in exp))

        rec = results["categories"][cat]["recovery"]
        if isinstance(rec, str):
            # basement's recovery is UNDEFINED under the registration, so the
            # panel states P3's own criterion instead of a number.
            sk = results["categories"][cat]["skill"]
            assert sk["WEATHER"] > sk["CLOCK"], (
                "basement stat text assumes P3's comparison holds")
            stat = "weather beat the calendar"
        else:
            stat = f"recovery {fmt_recovery(rec)}"

        if cat in verdict_by_cat:
            code, verdict = verdict_by_cat[cat]
            chip, kind = f"{code} {verdict}", verdict.lower()
        else:
            chip, kind = "no prediction", "none"

        panels.append({
            "cat": cat,
            "slot": CATS.index(cat),
            "actual": act,
            "registered": reg,
            "exploratory": exp,
            "ymax": ymax,
            "ymaxLabel": f"{round(ymax):,}",
            "stat": stat,
            "chip": chip,
            "chipKind": kind,
        })

    # ---- the daily basement series, on log1p ----------------------------
    rows = [r for r in csv.DictReader(
        (ROOT / "data" / "study_daily.csv").open(encoding="utf-8"))
        if DAILY_FROM <= r["day"] <= DAILY_TO]
    assert rows, "no daily rows in range"
    days = [r["day"] for r in rows]
    daily = [int(r["basement"]) for r in rows]

    peak_i = max(range(len(daily)), key=lambda i: daily[i])
    pd = date.fromisoformat(days[peak_i])
    peak_label = (f"{pd.day} {MONTH_ABBR[pd.month - 1]} {pd.year} · "
                  f"{daily[peak_i]:,} in one day")

    floor = math.expm1(diag["basement"]["trend_constant_log1p"])
    floor_label = f"registered model's floor · {round(floor):,} a day, all year"

    log_max = math.log1p(max(daily))

    def yfrac(v: float) -> float:
        return math.log1p(v) / log_max

    median_count = statistics.median(daily)
    floor_y, typical_y = yfrac(floor), yfrac(median_count)
    separation = abs(floor_y - typical_y)
    assert separation >= H15_MIN_SEPARATION, (
        f"H15: on the log scale the registered floor sits at "
        f"{floor_y:.3f} of plot height and the typical daily level at "
        f"{typical_y:.3f}; separation {separation:.3f} is below "
        f"{H15_MIN_SEPARATION}"
    )

    gridlines = [{"count": c, "label": f"{c:,}", "y": yfrac(c)}
                 for c in GRIDLINE_COUNTS]

    assert TRAIN_ENDS in days, f"{TRAIN_ENDS} not in the daily range"
    train_i = days.index(TRAIN_ENDS)

    first = date.fromisoformat(days[0])
    last = date.fromisoformat(days[-1])

    payload = {
        "stages": stages,
        "months": months,
        "monthLabels": month_labels(months),
        "cats": CATS,
        "huesLight": HUES_LIGHT,
        "huesDark": HUES_DARK,
        "rows": {
            "actual": actual_stack,
            "registered": reg_stack,
            "exploratory": exp_stack,
        },
        "countsMax": counts_max,
        "basementShare": shares,
        "panels": panels,
        "daily": {
            "values": daily,
            "max": max(daily),
            "scale": "log1p",
            "logMax": log_max,
            "gridlines": gridlines,
            "medianCount": median_count,
            "floorY": floor_y,
            "typicalY": typical_y,
            "separation": separation,
            "peakIndex": peak_i,
            "peakLabel": peak_label,
            "trainIndex": train_i,
            "trainLabel": TRAIN_LAST_DAY,
            "floor": floor,
            "floorLabel": floor_label,
            "axisLeft": f"{MONTH_ABBR[first.month - 1]} {first.year}",
            "axisRight": f"{MONTH_ABBR[last.month - 1]} {last.year}",
        },
    }

    template = ROOT / "viz" / "overview.template.html"
    text = template.read_text(encoding="utf-8")
    for ph in (DATA_PLACEHOLDER, PANELS_PLACEHOLDER):
        assert text.count(ph) == 1, f"template needs exactly one {ph}"

    # ensure_ascii=False so the printed strings appear in the page as the
    # characters they are, and can be matched against the sources by a test.
    page = text.replace(
        DATA_PLACEHOLDER,
        json.dumps(payload, separators=(",", ":"), ensure_ascii=False),
    ).replace(PANELS_PLACEHOLDER, panel_markup(panels))

    for token in FORBIDDEN:
        assert token not in page, f"page is not offline: contains {token!r}"

    out = ROOT / "viz" / "overview.html"
    out.write_text(page, encoding="utf-8")

    print(f"wrote {out} ({out.stat().st_size} bytes)")
    print()
    print("basement mean share, final stage:")
    print(f"  actual       {shares['labels']['actual']}%     "
          f"[results/frames.json]")
    print(f"  registered   {shares['labels']['registered'][-1]}%      "
          f"[results/frames.json]")
    print(f"  exploratory  {shares['labels']['exploratory'][-1]}%      "
          f"[results/exploratory_frames.json]")
    print()
    print("panels:")
    for p in panels:
        print(f"  {p['cat']:19s} {p['stat']:28s} {p['chip']:15s} "
              f"y-max {p['ymaxLabel']:>7s}")
    print()
    print(f"peak   {peak_label}          [data/study_daily.csv]")
    print(f"floor  {floor_label}   [results/trend_diagnostic.json]")
    print()
    print("flood strip, log1p scale, fractions of plot height:")
    for g in gridlines:
        print(f"  gridline {g['label']:>5s}  y = {g['y']:.4f}")
    print(f"  floor          y = {floor_y:.4f}")
    print(f"  typical day    y = {typical_y:.4f} "
          f"(median {median_count:g} a day)")
    print(f"  separation       = {separation:.4f} "
          f"(H15 threshold {H15_MIN_SEPARATION})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
