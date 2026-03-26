"""
Score → human-readable category translation layer.

The raw numeric score (0-100) is kept on the model.  This module provides a
single source of truth for mapping that score to a labelled category so that
every serializer and view returns a consistent `score_category` value.

Ranges
------
- **Suitable**            : 70 – 100
- **Potentially Suitable** : 40 – 69
- **Unsuitable**          : 0 – 39
"""

from __future__ import annotations

from typing import NamedTuple


class ScoreCategory(NamedTuple):
    key: str  # machine-friendly slug
    label: str  # human-friendly label


# Ordered from highest to lowest so the first match wins.
_THRESHOLDS: list[tuple[int, ScoreCategory]] = [
    (70, ScoreCategory("suitable", "Suitable")),
    (40, ScoreCategory("potentially_suitable", "Potentially Suitable")),
    (0, ScoreCategory("unsuitable", "Unsuitable")),
]


def get_score_category(score: int | float | None) -> ScoreCategory | None:
    """Return the category for a given numeric score, or *None* if the score
    is ``None`` (i.e. analysis not yet complete)."""
    if score is None:
        return None
    for threshold, category in _THRESHOLDS:
        if score >= threshold:
            return category
    # Defensive fallback (score < 0 shouldn't happen but just in case)
    return ScoreCategory("unsuitable", "Unsuitable")
