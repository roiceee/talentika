"""
Duplicate detection service for job applications.

Scores existing applications against incoming submission data using:
  - Fuzzy name matching            (rapidfuzz, weight 0.30)
  - Exact phone match              (weight 0.25)
  - Address field similarity       (rapidfuzz, weight 0.20)
  - SHA-256 file hash match        (weight 0.25)

Candidates are pre-filtered at the database level (same job_profile + at least
one strong signal present) before any Python-level scoring, keeping this
efficient for large datasets.
"""

import hashlib
from dataclasses import dataclass, field
from typing import Optional

from rapidfuzz import fuzz

# ---------------------------------------------------------------------------
# Weights must sum to 1.0
# ---------------------------------------------------------------------------
_WEIGHTS: dict[str, float] = {
    "name": 0.30,
    "phone": 0.25,
    "email": 0.20,
    "file_hash": 0.25,
}

# Applications scoring at or above this value are considered duplicates.
DUPLICATE_THRESHOLD: float = 0.75


@dataclass
class ScoredApplication:
    application: object  # JobApplication instance
    duplicate_score: float
    signals: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def compute_sha256(file_obj) -> str:
    """Return the SHA-256 hex digest of *file_obj* (a file-like object).

    Rewinds the file before and after reading so callers can still use it.
    """
    h = hashlib.sha256()
    file_obj.seek(0)
    for chunk in iter(lambda: file_obj.read(65_536), b""):
        h.update(chunk)
    file_obj.seek(0)
    return h.hexdigest()


def _name_score(first_name: str, last_name: str, candidate) -> float:
    """Token-sort ratio on the full name (case-insensitive)."""
    incoming = f"{first_name} {last_name}".lower().strip()
    existing = f"{candidate.first_name} {candidate.last_name}".lower().strip()
    return fuzz.token_sort_ratio(incoming, existing) / 100.0


def _file_hash_score(incoming_hash: Optional[str], candidate) -> float:
    """1.0 if any candidate attachment SHA-256 matches the incoming hash."""
    if not incoming_hash:
        return 0.0
    matched = candidate.attachments.filter(sha256_hash=incoming_hash).exists()
    return 1.0 if matched else 0.0


def _email_score(incoming_email: str, candidate) -> float:
    """1.0 if email matches (case-insensitive)."""
    if not incoming_email:
        return 0.0
    return 1.0 if (candidate.email or "").lower() == incoming_email.lower() else 0.0


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def find_duplicates(
    *,
    job_profile,
    first_name: str,
    last_name: str,
    phone: str,
    email: str = "",
    sha256_hash: Optional[str] = None,
    exclude_id=None,
    threshold: float = DUPLICATE_THRESHOLD,
) -> list[ScoredApplication]:
    """
    Scan existing applications for the given *job_profile* and return a list
    of :class:`ScoredApplication` objects (score >= *threshold*), sorted
    descending by score.

    Parameters
    ----------
    job_profile:
        A ``JobProfile`` model instance (or PK) to scope the search.
    first_name / last_name:
        Applicant name from the incoming submission.
    phone:
        Applicant phone (empty string is fine).
    email:
        Applicant email (empty string is fine).
    sha256_hash:
        SHA-256 hex digest of the uploaded resume (if any).
    exclude_id:
        UUID to exclude (used when re-checking a saved instance).
    threshold:
        Minimum score to include in results (default 0.75).
    """
    from .models import JobApplication

    phone = (phone or "").strip()

    # ------------------------------------------------------------------
    # DB-level pre-filter: same job_profile is mandatory.
    # We also narrow to rows that share at least one strong signal so we
    # avoid loading every application in a high-volume job_profile.
    # ------------------------------------------------------------------
    from django.db.models import Q

    candidates_qs = JobApplication.objects.filter(
        job_profile=job_profile
    ).prefetch_related("attachments")

    if exclude_id:
        candidates_qs = candidates_qs.exclude(id=exclude_id)

    # Narrow: exact phone OR file hash OR email match.
    narrowing_filter = Q()
    if phone:
        narrowing_filter |= Q(phone=phone)
    if sha256_hash:
        narrowing_filter |= Q(attachments__sha256_hash=sha256_hash)
    if email:
        narrowing_filter |= Q(email__iexact=email)

    if narrowing_filter:
        candidates_qs = candidates_qs.filter(narrowing_filter).distinct()

    # ------------------------------------------------------------------
    # Python-level scoring
    # ------------------------------------------------------------------
    results: list[ScoredApplication] = []

    for candidate in candidates_qs:
        signals: dict[str, float] = {
            "name": _name_score(first_name, last_name, candidate),
            "phone": (
                1.0 if phone and (candidate.phone or "").strip() == phone else 0.0
            ),
            "email": _email_score(email, candidate),
            "file_hash": _file_hash_score(sha256_hash, candidate),
        }

        score = sum(_WEIGHTS[k] * v for k, v in signals.items())

        if score >= threshold:
            results.append(
                ScoredApplication(
                    application=candidate,
                    duplicate_score=round(score, 4),
                    signals=signals,
                )
            )

    results.sort(key=lambda x: x.duplicate_score, reverse=True)
    return results


def is_duplicate(
    *,
    job_profile,
    first_name: str,
    last_name: str,
    phone: str,
    email: str = "",
    sha256_hash: Optional[str] = None,
    exclude_id=None,
    threshold: float = DUPLICATE_THRESHOLD,
) -> bool:
    """Convenience wrapper — returns ``True`` if any duplicate is found."""
    return bool(
        find_duplicates(
            job_profile=job_profile,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            email=email,
            sha256_hash=sha256_hash,
            exclude_id=exclude_id,
            threshold=threshold,
        )
    )
