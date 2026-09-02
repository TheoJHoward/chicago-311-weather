"""Checks on the single-screen overview page.

test_overview_figures_match_sources deliberately does not import
viz/build_overview.py. It recomputes every printed figure from the committed
sources on its own, so a mistake in the build script cannot make the test agree
with it.

It compares against the page's parsed data block, not against the raw text. A
bare substring search is not a check here: the embedded JSON puts a comma
between adjacent array values, so a string like "6,999" occurs by accident from
a 6 followed by a 999, and a search for it passes whether or not the figure is
on the page.
"""

from __future__ import annotations

import csv
import json
import math
import re
import statistics
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "viz" / "overview.html"
RESULTS = ROOT / "results"

CATS = ["basement", "pothole", "rodent", "graffiti", "tree debris",
        "abandoned vehicle"]
PANEL_ORDER = ["pothole", "rodent", "basement", "graffiti", "tree debris",
               "abandoned vehicle"]
MONTH_ABBR = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MINUS = "−"
GRIDLINE_COUNTS = [10, 100, 1000]
SMOOTH_WINDOW = 7
COMP_W = 1920
COMP_H = 912



@pytest.fixture(scope="module")
def page() -> str:
    return PAGE.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def payload(page) -> dict:
    m = re.search(
        r'<script type="application/json" id="payload">(.*?)</script>',
        page, re.S)
    assert m, "no embedded payload block"
    return json.loads(m.group(1))


def load(name: str):
    return json.loads((RESULTS / name).read_text(encoding="utf-8"))


def css_rules(text: str):
    style = re.search(r"<style>(.*?)</style>", text, re.S)
    assert style, "page has no style block"
    body = re.sub(r"/\*.*?\*/", "", style.group(1), flags=re.S)
    return [(sel.strip(), decl) for sel, decl in
            re.findall(r"([^{}]+)\{([^{}]*)\}", body)]


def declarations(decl: str):
    out = []
    for part in decl.split(";"):
        if ":" in part:
            prop, val = part.split(":", 1)
            out.append((prop.strip().lower(), val.strip().lower()))
    return out


def test_overview_offline(page):
    for token in ["http", "src=", "@import"]:
        assert token not in page, token


def test_overview_composition(page):
    """The page is a fixed composition scaled to the frame, not a layout that
    compresses. Below the reflow width it becomes an ordinary document."""
    rules = css_rules(page)

    comp = [d for sel, d in rules if sel == ".page"]
    assert comp, "no .page rule"
    props = dict(declarations(comp[0]))
    assert props.get("width") == f"{COMP_W}px", props.get("width")
    assert props.get("height") == f"{COMP_H}px", props.get("height")
    assert props.get("overflow") == "hidden", props.get("overflow")
    assert props.get("transform-origin") == "top left", props

    stage = [d for sel, d in rules if sel == ".stage"]
    assert stage, "no .stage rule"
    sprops = dict(declarations(stage[0]))
    assert sprops.get("position") == "fixed", sprops
    assert sprops.get("overflow") == "hidden", sprops

    # the scale is min(viewport width / 1920, viewport height / 912)
    fit = re.search(r"function fit\(\)\s*\{.*?\n\}", page, re.S)
    assert fit, "no fit function"
    body = fit.group(1) if fit.groups() else fit.group(0)
    scale = re.search(r"min\((.*?)\);", body, re.S)
    assert scale, "no min() scale expression: " + body
    expr = scale.group(1)
    assert f"/ {COMP_W}" in expr, expr
    assert f"/ {COMP_H}" in expr, expr

    # a composition stated in pixels cannot also depend on the viewport
    style = re.search(r"<style>(.*?)</style>", page, re.S).group(1)
    units = re.findall(r"[0-9.]+(?:vh|vw|dvh|dvw)\b", style)
    assert not units, units

    assert re.search(r"@media \(max-width: 99\d px?\)|@media \(max-width: 999px\)",
                     style), "no reflow media query"


def test_overview_no_loop(page):
    """Playback must stop at the last stage, not wrap around."""
    tick = re.search(r"function tick\(\)\s*\{(.*?)\n\}", page, re.S)
    assert tick, "no tick function found"
    body = tick.group(1)
    assert "%" not in body, "stage advance uses a modulo: " + body
    assert re.search(r"stage\s*>=\s*N_STAGE\s*-\s*1", body), \
        "no clamp against the last stage: " + body
    assert not re.search(r"stage\s*=\s*0", body), \
        "tick resets the stage: " + body


def test_overview_figures_match_sources(payload):
    frames = load("frames.json")
    expl = load("exploratory_frames.json")
    results = load("results.json")
    expl_res = load("exploratory_no_trend.json")
    diag = load("trend_diagnostic.json")

    fc, ec = frames["categories"], expl["categories"]
    n_month = len(frames["months"])
    last = len(frames["stages"]) - 1

    # --- basement mean share, each row, final stage ---------------------
    def share_of(block, get) -> float:
        acc = 0.0
        for i in range(n_month):
            vals = {c: get(block[c])[i] for c in CATS}
            total = sum(vals.values())
            acc += vals["basement"] / total if total else 0.0
        return acc / n_month

    def label(v: float) -> str:
        p = v * 100
        return f"{p:.1f}" if p < 10 else str(round(p))

    labels = payload["basementShare"]["labels"]
    assert labels["actual"] == label(share_of(fc, lambda b: b["actual"]))
    assert labels["registered"][last] == label(
        share_of(fc, lambda b: b["model"][last]))
    assert labels["exploratory"][last] == label(
        share_of(ec, lambda b: b["model"][last]))

    # --- per panel: stat, chip, y-maximum -------------------------------
    verdicts = {v["category"]: (v["code"], v["verdict"])
                for v in results["verdicts"]}
    panels = {p["cat"]: p for p in payload["panels"]}
    assert [p["cat"] for p in payload["panels"]] == PANEL_ORDER

    for cat in PANEL_ORDER:
        p = panels[cat]
        rec = results["categories"][cat]["recovery"]
        rec_x = expl_res["categories"][cat]["recovery"]
        if isinstance(rec, str):
            assert rec == "UNDEFINED", rec
            # the phrase claims the criterion held in both analyses
            sk = results["categories"][cat]["skill"]
            sx = expl_res["categories"][cat]["skill"]
            assert sk["WEATHER"] > sk["CLOCK"], (
                "registered: weather did not beat the calendar")
            assert sx["WEATHER"] > 0 and sx["CLOCK"] > 0, (
                "exploratory skills are not both positive")
            assert not isinstance(rec_x, str) and rec_x > 1.0, rec_x
            assert p["stat"] == "weather beat the calendar in both analyses", \
                p["stat"]
        else:
            expected = (
                "recovery " + f"{rec:.2f}".replace("-", MINUS)
                + " registered · " + f"{rec_x:.2f}".replace("-", MINUS)
                + " exploratory"
            )
            assert p["stat"] == expected, (cat, p["stat"], expected)

        if cat in verdicts:
            code, verdict = verdicts[cat]
            assert p["chip"] == f"{code} {verdict}", (cat, p["chip"])
            assert p["chipKind"] == verdict.lower(), (cat, p["chipKind"])
        else:
            assert p["chip"] == "no prediction", (cat, p["chip"])
            assert p["chipKind"] == "none", (cat, p["chipKind"])

        ymax = max(
            max(fc[cat]["actual"]),
            max(max(r) for r in fc[cat]["model"]),
            max(max(r) for r in ec[cat]["model"]),
        )
        assert p["ymax"] == pytest.approx(ymax), (cat, p["ymax"], ymax)
        assert p["ymaxLabel"] == f"{round(ymax):,}", (cat, p["ymaxLabel"])

    # --- the peak day and the registered floor --------------------------
    rows = [r for r in csv.DictReader(
        (ROOT / "data" / "study_daily.csv").open(encoding="utf-8"))
        if "2025-07-01" <= r["day"] <= "2026-08-31"]
    daily = [int(r["basement"]) for r in rows]
    assert payload["daily"]["values"] == daily
    peak_i = max(range(len(daily)), key=lambda i: daily[i])
    pd = date.fromisoformat(rows[peak_i]["day"])
    peak = (f"{pd.day} {MONTH_ABBR[pd.month - 1]} {pd.year} · "
            f"{daily[peak_i]:,} in one day")
    assert payload["daily"]["peakIndex"] == peak_i
    assert payload["daily"]["peakLabel"] == peak, payload["daily"]["peakLabel"]

    floor = math.expm1(diag["basement"]["trend_constant_log1p"])
    expected_floor = (f"registered model's floor · {round(floor):,} "
                      f"a day, all year")
    assert payload["daily"]["floor"] == pytest.approx(floor)
    assert payload["daily"]["floorLabel"] == expected_floor, \
        payload["daily"]["floorLabel"]

    # --- the flood strip's log scale and its gridlines -------------------
    log_max = math.log1p(max(daily))
    assert payload["daily"]["scale"] == "log1p", payload["daily"]["scale"]
    assert payload["daily"]["logMax"] == pytest.approx(log_max)

    grid = payload["daily"]["gridlines"]
    assert [g["count"] for g in grid] == GRIDLINE_COUNTS, grid
    for g in grid:
        assert g["label"] == f"{g['count']:,}", g
        assert g["y"] == pytest.approx(math.log1p(g["count"]) / log_max), g

    # the floor must stay visibly clear of the typical daily level
    typical = statistics.median(daily)
    assert payload["daily"]["medianCount"] == pytest.approx(typical)
    floor_y = math.log1p(floor) / log_max
    typical_y = math.log1p(typical) / log_max
    assert payload["daily"]["floorY"] == pytest.approx(floor_y)
    assert payload["daily"]["typicalY"] == pytest.approx(typical_y)
    assert abs(floor_y - typical_y) >= 0.08, (
        f"floor at {floor_y:.3f} and typical level at {typical_y:.3f} "
        f"are not visibly separated")

    # --- the seven-day trailing mean drawn over the raw series ----------
    window = payload["daily"]["smoothWindow"]
    assert window == SMOOTH_WINDOW, window
    expected_mean = []
    for i in range(len(daily)):
        chunk = daily[max(0, i - window + 1):i + 1]
        expected_mean.append(sum(chunk) / len(chunk))
    smoothed = payload["daily"]["smoothed"]
    assert len(smoothed) == len(daily), (len(smoothed), len(daily))
    for i, (got, want) in enumerate(zip(smoothed, expected_mean)):
        assert got == pytest.approx(want, abs=0.01), (i, got, want)
    assert payload["daily"]["smoothedMax"] == pytest.approx(
        max(expected_mean), abs=0.01), payload["daily"]["smoothedMax"]
    # the mean must flatten the series it smooths, not reproduce it
    assert max(expected_mean) < max(daily), (max(expected_mean), max(daily))


def test_overview_stat_lines_carry_both_analyses(page):
    """Every panel's second line names the exploratory value, so the
    comparison the narration makes is on the page rather than off it."""
    stats = re.findall(r'<div class="p-stat">([^<]*)</div>', page)
    assert len(stats) == len(PANEL_ORDER), stats
    for s in stats:
        assert "exploratory" in s or "both analyses" in s, s


def test_overview_strip_draws_raw_and_mean(page):
    """The flood strip carries two lines: each day, and the seven-day mean."""
    assert 'class="why-raw"' in page
    assert 'class="why-mean"' in page
    assert "Light line is each day; dark line is the seven-day average." in page

    rules = css_rules(page)
    raw = [dict(declarations(d)) for sel, d in rules if sel == ".why-raw"]
    mean = [dict(declarations(d)) for sel, d in rules if sel == ".why-mean"]
    assert raw and "color-mix" in raw[0].get("stroke", ""), raw
    assert mean and mean[0].get("stroke") == "var(--accent)", mean


def test_overview_ymax_label_has_a_halo(page):
    """A line can cross the y-maximum label, so the glyphs carry a
    surface-coloured halo painted behind them."""
    rules = css_rules(page)
    ymax = [dict(declarations(d)) for sel, d in rules if sel == ".p-ymax"]
    assert ymax, "no .p-ymax rule"
    props = ymax[0]
    assert props.get("paint-order") == "stroke fill", props
    assert "var(--surface)" in props.get("-webkit-text-stroke", ""), props


def test_overview_descriptor_states_the_scale(page):
    assert "Log scale, the same one the study scores on." in page


def test_overview_panel_headers_two_lines(page):
    """Each panel's name and stat are distinct nodes, in that order, and the
    name does not wrap."""
    panels = re.findall(
        r'<div class="panel" data-cat="([^"]+)">(.*?)<div class="p-plot">',
        page, re.S)
    assert [c for c, _ in panels] == PANEL_ORDER, [c for c, _ in panels]

    for cat, block in panels:
        name = re.search(r'<span class="p-nm">([^<]*)</span>', block)
        stat = re.search(r'<div class="p-stat">([^<]*)</div>', block)
        assert name, f"{cat}: no name node"
        assert stat, f"{cat}: no stat node"
        assert name.group(1) == cat, (cat, name.group(1))
        # distinct nodes, name first
        assert name.start() < stat.start(), f"{cat}: stat precedes the name"
        # the stat is not inside the header line the name sits on
        head = re.search(r'<div class="p-head">(.*?)</div>\s*<div class="p-stat"',
                         block, re.S)
        assert head, f"{cat}: stat is not a sibling after the header line"
        assert "p-stat" not in head.group(1), f"{cat}: stat is inside p-head"

    rules = css_rules(page)
    nm = [dict(declarations(d)) for sel, d in rules if sel == ".p-nm"]
    assert nm and nm[0].get("white-space") == "nowrap", nm
