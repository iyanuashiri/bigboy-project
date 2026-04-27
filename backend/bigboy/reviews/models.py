from django.conf import settings
from django.db import models

from bigboy.subjects.models import Bite, Subject


class BiteReviewState(models.Model):
    """Lightweight spaced repetition schedule per (account, bite)."""

    class Grade(models.TextChoices):
        AGAIN = 'again', 'Again'
        HARD = 'hard', 'Hard'
        GOOD = 'good', 'Good'
        EASY = 'easy', 'Easy'

    account = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bite_review_states',
    )
    bite = models.ForeignKey(
        Bite,
        on_delete=models.CASCADE,
        related_name='review_states',
    )
    interval_days = models.PositiveSmallIntegerField(default=1)
    repetitions = models.PositiveIntegerField(default=0)
    next_review_at = models.DateTimeField(db_index=True)
    last_reviewed_at = models.DateTimeField(null=True, blank=True)
    last_grade = models.CharField(
        max_length=8,
        choices=Grade.choices,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=('account', 'bite'), name='reviews_bitereviewstate_account_bite_uniq'),
        ]
        indexes = [
            models.Index(fields=('account', 'next_review_at')),
        ]

    def __str__(self):
        return f'{self.account_id} bite {self.bite_id}'


class SubjectWeeklyGoal(models.Model):
    """Simple weekly bite-completion target per enrolled subject."""

    account = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subject_weekly_goals',
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='weekly_goals',
    )
    weekly_bite_target = models.PositiveSmallIntegerField(default=5)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('account', 'subject'),
                name='reviews_subjectweeklygoal_account_subject_uniq',
            ),
        ]

    def __str__(self):
        return f'{self.account_id} subject {self.subject_id} target {self.weekly_bite_target}'
