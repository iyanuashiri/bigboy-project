from django.test import TestCase
from django.utils import timezone

from bigboy.accounts.models import Account
from bigboy.reviews.models import BiteReviewState
from bigboy.reviews.services.review_hooks import schedule_initial_review_after_bite_learned
from bigboy.subjects.models import Bite, Enrollment, Subject, Topic


def _user(suffix: str) -> Account:
    return Account.objects.create_user(
        phone_number=f'+234800{suffix}',
        password='test-pass-123',
        first_name='Hook',
        last_name='Test',
    )


class ScheduleInitialReviewTests(TestCase):
    def setUp(self):
        self.account = _user('40004001')
        self.subject = Subject.objects.create_subject_by_user(name='HS', description='d')
        Enrollment.objects.create(account=self.account, subject=self.subject)
        self.topic = Topic.objects.create(
            subject=self.subject,
            name='HT',
            description='d',
            content='c',
        )
        self.bite = Bite.objects.create(topic=self.topic, name='hb', bite='body')

    def test_creates_or_updates_review_state(self):
        schedule_initial_review_after_bite_learned(account=self.account, bite_id=self.bite.id)
        st = BiteReviewState.objects.get(account=self.account, bite=self.bite)
        self.assertGreater(st.next_review_at, timezone.now())

    def test_second_call_keeps_single_row(self):
        schedule_initial_review_after_bite_learned(account=self.account, bite_id=self.bite.id)
        schedule_initial_review_after_bite_learned(account=self.account, bite_id=self.bite.id)
        self.assertEqual(BiteReviewState.objects.filter(account=self.account, bite=self.bite).count(), 1)
