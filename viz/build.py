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


def main() -> int:
    out = ROOT / "viz" / "year_strip.html"
    build(ROOT / "viz" / "year_strip.template.html",
          ROOT / "results" / "frames.json",
          out)
    print(f"wrote {out} ({out.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
