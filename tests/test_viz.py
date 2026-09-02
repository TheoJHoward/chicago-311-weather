"""Checks on the built visualization pages.

These read the generated HTML. They assert the construction that makes a page
unable to scroll — a viewport-height flex column with hidden overflow, and a
plot band whose height is inherited rather than fixed in pixels — rather than a
rendered height, which would need a browser this suite does not have.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
VIZ = ROOT / "viz"

STRIP_PAGES = ["year_strip.html", "year_strip_exploratory.html"]
FORBIDDEN_TOKENS = ["http", "src=", "@import"]

# Selectors that carry the plot band and the bars. A fixed pixel height on any
# of these is what breaks the fit, so none of them may declare one.
FLEXIBLE = (".plot", ".bars", ".bar", ".col", ".row", ".page")

ROOT_SELECTOR = ".page"
VIEWPORT_HEIGHTS = {"100vh", "100dvh"}


def built_pages() -> list[Path]:
    return sorted(p for p in VIZ.glob("*.html")
                  if not p.name.endswith(".template.html"))


def css_rules(text: str) -> list[tuple[str, str]]:
    """Every (selector, declaration-block) pair in the page's style element."""
    style = re.search(r"<style>(.*?)</style>", text, re.S)
    assert style, "page has no style block"
    body = re.sub(r"/\*.*?\*/", "", style.group(1), flags=re.S)
    return [(sel.strip(), decl) for sel, decl in
            re.findall(r"([^{}]+)\{([^{}]*)\}", body)]


def declarations(decl: str) -> list[tuple[str, str]]:
    out = []
    for part in decl.split(";"):
        if ":" in part:
            prop, val = part.split(":", 1)
            out.append((prop.strip().lower(), val.strip().lower()))
    return out


@pytest.mark.parametrize("name", STRIP_PAGES)
def test_pages_declare_viewport_fit(name):
    path = VIZ / name
    rules = css_rules(path.read_text(encoding="utf-8"))

    root = [d for sel, d in rules if sel == ROOT_SELECTOR]
    assert root, f"{name}: no {ROOT_SELECTOR} rule"
    props = dict(declarations(root[0]))
    assert props.get("height") in VIEWPORT_HEIGHTS, (
        f"{name}: {ROOT_SELECTOR} height is {props.get('height')!r}, "
        f"expected one of {sorted(VIEWPORT_HEIGHTS)}"
    )
    assert props.get("overflow") == "hidden", (
        f"{name}: {ROOT_SELECTOR} overflow is {props.get('overflow')!r}, "
        f"expected 'hidden'"
    )

    offenders = []
    for sel, decl in rules:
        if not any(token in sel for token in FLEXIBLE):
            continue
        for prop, val in declarations(decl):
            if prop in ("height", "min-height") and re.search(r"\d\s*px", val):
                offenders.append(f"{sel} {{ {prop}: {val} }}")
    assert not offenders, (
        f"{name}: fixed pixel height on the plot band or bars — "
        + "; ".join(offenders)
    )


EXPECTED_PAGES = {
    "overview.html",
    "slider.html",
    "year_ring.html",
    "year_strip.html",
    "year_strip_exploratory.html",
}


def test_no_external_references():
    pages = built_pages()
    assert {p.name for p in pages} == EXPECTED_PAGES, [p.name for p in pages]
    for path in pages:
        text = path.read_text(encoding="utf-8")
        for token in FORBIDDEN_TOKENS:
            assert token not in text, f"{path.name}: {token}"
