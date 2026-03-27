"""
Category label lookup layer.

The AI now returns a category key directly ("suitable", "potentially_suitable",
or "unsuitable").  This module maps those keys to human-readable labels so that
every serializer and view returns a consistent ``score_category`` value.

Categories
----------
- **Suitable**             — Strong fit; meets key requirements well
- **Potentially Suitable** — Partial fit; meets some requirements but has notable gaps
- **Unsuitable**           — Poor fit; does not meet core requirements
"""

from __future__ import annotations

from typing import NamedTuple


class ScoreCategory(NamedTuple):
    key: str  # machine-friendly slug
    label: str  # human-friendly label


_CATEGORIES: dict[str, ScoreCategory] = {
    "suitable": ScoreCategory("suitable", "Suitable"),
    "potentially_suitable": ScoreCategory("potentially_suitable", "Potentially Suitable"),
    "unsuitable": ScoreCategory("unsuitable", "Unsuitable"),
}


def get_score_category(key: str | None) -> ScoreCategory | None:
    """Return the ScoreCategory for a given key, or *None* if the key is
    ``None`` or unrecognised (i.e. analysis not yet complete)."""
    if key is None:
        return None
    return _CATEGORIES.get(key)
