"""Weekly bite-completion progress for subject goals."""

from __future__ import annotations

from datetime import datetime, time, timedelta

from django.utils import timezone

from bigboy.subjects.models import Checkpoint


def _week_start(now=None):
    now = now or timezone.now()
    d = timezone.localdate(now)
    monday = d - timedelta(days=d.weekday())
    naive = datetime.combine(monday, time.min)
    if timezone.is_naive(now):
        return naive
    return timezone.make_aware(naive, timezone.get_current_timezone())


def bites_completed_this_week(*, account, subject_id: int) -> int:
    start = _week_start()
    return Checkpoint.objects.filter(
        account=account,
        bite__topic__subject_id=subject_id,
        status=Checkpoint.Status.COMPLETED,
        date_completed__gte=start,
    ).count()
