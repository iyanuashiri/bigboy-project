"""Simple non-predictive spaced repetition intervals (Again / Hard / Good / Easy)."""

from __future__ import annotations

from datetime import timedelta

from django.utils import timezone

MAX_INTERVAL_DAYS = 45


def apply_grade(
    *,
    grade: str,
    interval_days: int,
    repetitions: int,
) -> tuple[int, int, timedelta]:
    """
    Return (new_interval_days, new_repetitions, delta_until_next_review).
    """
    g = (grade or '').strip().lower()
    if g == 'again':
        return 1, 0, timedelta(days=1)
    rep = repetitions + 1
    base = max(1, int(interval_days))
    if g == 'hard':
        nxt = min(MAX_INTERVAL_DAYS, max(1, int(base * 1.35)))
        return nxt, rep, timedelta(days=nxt)
    if g == 'easy':
        nxt = min(MAX_INTERVAL_DAYS, max(2, int(base * 2.5)))
        return nxt, rep, timedelta(days=nxt)
    # good
    nxt = min(MAX_INTERVAL_DAYS, max(1, int(base * 2.0)))
    return nxt, rep, timedelta(days=nxt)


def initial_review_timedelta() -> timedelta:
    """First review shortly after the bite was learned."""
    return timedelta(days=1)
