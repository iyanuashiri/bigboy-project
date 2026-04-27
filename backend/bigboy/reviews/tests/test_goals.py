from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from bigboy.accounts.models import Account
from bigboy.reviews.services.goals import bites_completed_this_week
from bigboy.subjects.models import Bite, Checkpoint, Enrollment, Subject, Topic


def _account(phone_suffix: str) -> Account:
    return Account.objects.create_user(
        phone_number=f'+234800{phone_suffix}',
        password='test-pass-123',
        first_name='Test',
        last_name='User',
    )


class WeeklyBiteProgressTests(TestCase):
    def setUp(self):
        self.account = _account('10001001')
        self.subject = Subject.objects.create_subject_by_user(name='S1', description='d')
        Enrollment.objects.create(account=self.account, subject=self.subject)
        self.topic = Topic.objects.create(
            subject=self.subject,
            name='T1',
            description='td',
            content='content',
        )
        self.bite = Bite.objects.create(topic=self.topic, name='b1', bite='body')

    def test_counts_completed_checkpoints_this_week(self):
        self.assertEqual(
            bites_completed_this_week(account=self.account, subject_id=self.subject.id),
            0,
        )
        Checkpoint.objects.create(
            bite=self.bite,
            account=self.account,
            status=Checkpoint.Status.COMPLETED,
        )
        self.assertEqual(
            bites_completed_this_week(account=self.account, subject_id=self.subject.id),
            1,
        )

    def test_ignores_other_subject(self):
        other = Subject.objects.create_subject_by_user(name='S2', description='d')
        t2 = Topic.objects.create(subject=other, name='T2', description='d', content='c')
        b2 = Bite.objects.create(topic=t2, name='b2', bite='x')
        Checkpoint.objects.create(bite=b2, account=self.account, status=Checkpoint.Status.COMPLETED)
        self.assertEqual(
            bites_completed_this_week(account=self.account, subject_id=self.subject.id),
            0,
        )

    def test_old_checkpoint_excluded_via_manual_date(self):
        Checkpoint.objects.create(
            bite=self.bite,
            account=self.account,
            status=Checkpoint.Status.COMPLETED,
        )
        cp = Checkpoint.objects.get(bite=self.bite, account=self.account)
        old = timezone.now() - timedelta(days=20)
        Checkpoint.objects.filter(pk=cp.pk).update(date_completed=old)
        self.assertEqual(
            bites_completed_this_week(account=self.account, subject_id=self.subject.id),
            0,
        )
