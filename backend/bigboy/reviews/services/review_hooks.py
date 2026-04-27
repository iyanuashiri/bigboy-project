"""Integrate review scheduling with lesson progress."""

from __future__ import annotations

import logging

from django.db import transaction
from django.utils import timezone

from bigboy.reviews.models import BiteReviewState
from bigboy.reviews.services.scheduling import initial_review_timedelta

logger = logging.getLogger(__name__)


def schedule_initial_review_after_bite_learned(*, account, bite_id: int) -> None:
    """
    After a bite is marked complete in the lesson path, queue it for spaced review.

    Idempotent: if a row already exists, refresh next_review_at only when still in the future
    and user has not graded yet (repetitions == 0 and last_grade empty) — keep simple: update_or_create.
    """
    try:
        with transaction.atomic():
            next_at = timezone.now() + initial_review_timedelta()
            BiteReviewState.objects.update_or_create(
                account=account,
                bite_id=bite_id,
                defaults={
                    'interval_days': 1,
                    'repetitions': 0,
                    'next_review_at': next_at,
                    'last_grade': '',
                },
            )
    except Exception as exc:  # noqa: BLE001
        logger.exception('Failed to schedule review for bite %s: %s', bite_id, exc)
