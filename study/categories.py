"""The six categories, their keyword rules, and their roles.

A category is the union of every sr_type whose lowercase form contains the
keyword. The alternates are used only to build an informative message when a
keyword matches nothing; they never widen the rule.
"""

from __future__ import annotations

CATEGORIES: list[dict] = [
    {
        "name": "pothole",
        "keyword": "pothole",
        "role": "confirmatory",
        "alternates": ["pavement", "street cut"],
    },
    {
        "name": "rodent",
        "keyword": "rodent",
        "role": "confirmatory",
        "alternates": ["rat", "baiting"],
    },
    {
        "name": "basement",
        "keyword": "water in basement",
        "role": "confirmatory",
        "alternates": ["basement", "sewer", "flood", "water on street"],
    },
    {
        "name": "graffiti",
        "keyword": "graffiti",
        "role": "confirmatory",
        "alternates": ["vandal"],
    },
    {
        "name": "tree debris",
        "keyword": "tree debris",
        "role": "exploratory",
        "alternates": ["tree", "debris", "storm"],
    },
    {
        "name": "abandoned vehicle",
        "keyword": "abandoned vehicle",
        "role": "exploratory",
        "alternates": ["vehicle"],
    },
]

CATEGORY_NAMES = [c["name"] for c in CATEGORIES]
CONFIRMATORY = [c["name"] for c in CATEGORIES if c["role"] == "confirmatory"]


def matches(keyword: str, sr_types: list[str]) -> list[str]:
    """Every sr_type whose lowercase form contains the lowercase keyword."""
    k = keyword.lower()
    return [s for s in sr_types if k in s.lower()]
