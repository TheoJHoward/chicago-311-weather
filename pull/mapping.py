"""Apply the registration's keyword rule to the enumerated service-request types.

Reads data/sr_types.csv and writes PREREG_MAPPING.md. If a category's keyword
matches no type, prints the fifteen highest-count types containing any of that
category's alternate keywords and exits 1 without writing the mapping.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from study.categories import CATEGORIES, matches  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def load() -> list[tuple[str, int]]:
    with (ROOT / "data" / "sr_types.csv").open(encoding="utf-8") as fh:
        return [(r["sr_type"], int(r["n"])) for r in csv.DictReader(fh)]


def main() -> int:
    rows = load()
    counts = dict(rows)
    sr_types = [s for s, _ in rows]

    resolved = []
    for cat in CATEGORIES:
        hit = matches(cat["keyword"], sr_types)
        if not hit:
            print(f"H1: category '{cat['name']}' keyword "
                  f"'{cat['keyword']}' matched zero sr_type strings.",
                  file=sys.stderr)
            near = [
                (s, counts[s])
                for s in sr_types
                if any(a.lower() in s.lower() for a in cat["alternates"])
            ]
            near.sort(key=lambda r: -r[1])
            print(f"Alternates: {', '.join(cat['alternates'])}", file=sys.stderr)
            for s, n in near[:15]:
                print(f"  {n:>10,}  {s}", file=sys.stderr)
            if not near:
                print("  (no sr_type contains any alternate keyword)",
                      file=sys.stderr)
            return 1
        hit.sort(key=lambda s: (-counts[s], s))
        resolved.append((cat, hit))

    lines = [
        "# Category mapping",
        "",
        "Produced mechanically from the keyword rule in PREREG.md, applied to "
        "the all-time per-type counts in data/sr_types.csv. A category is the "
        "union of every sr_type whose lowercase form contains the keyword.",
        "",
        "| Category | Role | Keyword | Matched sr_type | All-time count |",
        "|---|---|---|---|---|",
    ]
    for cat, hit in resolved:
        for i, s in enumerate(hit):
            name = cat["name"] if i == 0 else ""
            role = cat["role"] if i == 0 else ""
            kw = f"`{cat['keyword']}`" if i == 0 else ""
            lines.append(f"| {name} | {role} | {kw} | {s} | {counts[s]:,} |")
    lines += [
        "",
        f"Types enumerated: {len(sr_types)}. "
        f"All-time records across all types: {sum(counts.values()):,}.",
        "",
        "Category totals (sum of matched types, all time):",
        "",
        "| Category | Types matched | All-time count |",
        "|---|---|---|",
    ]
    for cat, hit in resolved:
        lines.append(
            f"| {cat['name']} | {len(hit)} | {sum(counts[s] for s in hit):,} |"
        )
    lines.append("")

    out = ROOT / "PREREG_MAPPING.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out}")
    for cat, hit in resolved:
        print(f"  {cat['name']}: {len(hit)} type(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
