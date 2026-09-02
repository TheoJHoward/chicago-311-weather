"""Embed results/frames.json into the year-strip template.

The template carries the layout; this script substitutes the single data
placeholder and writes viz/year_strip.html. No other transformation is applied,
so every number on the page is the number the study run wrote.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLACEHOLDER = "__FRAMES_JSON__"
FORBIDDEN = ["http", "src=", "@import"]


def build(template: Path, frames: Path, out: Path) -> None:
    text = template.read_text(encoding="utf-8")
    assert text.count(PLACEHOLDER) == 1, "template needs exactly one placeholder"
    data = json.loads(frames.read_text(encoding="utf-8"))
    page = text.replace(PLACEHOLDER, json.dumps(data, separators=(",", ":")))
    for token in FORBIDDEN:
        assert token not in page, f"page is not offline: contains {token!r}"
    out.write_text(page, encoding="utf-8")


# page name -> the results file its data constant is taken from
PAGES = {
    "year_strip": "frames.json",
    "year_ring": "frames.json",
    "year_strip_exploratory": "exploratory_frames.json",
}


def build_slider(template: Path, grid: Path, out: Path) -> None:
    """The slider toy carries two constants in its prose as well as its data,
    so both are substituted from the same file the grid came from."""
    text = template.read_text(encoding="utf-8")
    data = json.loads(grid.read_text(encoding="utf-8"))
    page = (text
            .replace("__GRID_JSON__", json.dumps(data, separators=(",", ":")))
            .replace("__WIND__", f"{data['wind']:.2f}")
            .replace("__TLAST__", data["t_last_training_day"]))
    for token in FORBIDDEN:
        assert token not in page, f"page is not offline: contains {token!r}"
    for left in ["__GRID_JSON__", "__WIND__", "__TLAST__"]:
        assert left not in page, f"placeholder {left} not substituted"
    out.write_text(page, encoding="utf-8")


def main() -> int:
    for name, data_file in PAGES.items():
        template = ROOT / "viz" / f"{name}.template.html"
        data = ROOT / "results" / data_file
        if not template.exists() or not data.exists():
            continue
        out = ROOT / "viz" / f"{name}.html"
        build(template, data, out)
        print(f"wrote {out} ({out.stat().st_size} bytes) from {data_file}")

    slider_t = ROOT / "viz" / "slider.template.html"
    slider_g = ROOT / "results" / "slider_grid.json"
    if slider_t.exists() and slider_g.exists():
        out = ROOT / "viz" / "slider.html"
        build_slider(slider_t, slider_g, out)
        print(f"wrote {out} ({out.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
