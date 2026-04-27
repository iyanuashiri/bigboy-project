from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from bigboy.accounts.models import Account
from bigboy.reviews.models import BiteReviewState, SubjectWeeklyGoal
from bigboy.subjects.models import Bite, Enrollment, Subject, Topic


def _user(suffix: str) -> Account:
    return Account.objects.create_user(
        phone_number=f'+234800{suffix}',
        password='test-pass-123',
        first_name='Api',
        last_name='Test',
    )


class ReviewDueAndGradeAPITests(TestCase):
    def setUp(self):
        self.user = _user('20002001')
        self.token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

        self.subject = Subject.objects.create_subject_by_user(name='Sub', description='d')
        Enrollment.objects.create(account=self.user, subject=self.subject)
        self.topic = Topic.objects.create(
            subject=self.subject,
            name='Top',
            description='d',
            content='c',
        )
        self.bite = Bite.objects.create(topic=self.topic, name='B', bite='text')
        self.state = BiteReviewState.objects.create(
            account=self.user,
            bite=self.bite,
            interval_days=1,
            repetitions=0,
            next_review_at=timezone.now() - timedelta(hours=1),
        )

    def test_due_list_returns_scheduled_bite(self):
        r = self.client.get('/api/v1/reviews/due/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(len(r.data), 1)
        self.assertEqual(r.data[0]['bite'], self.bite.id)

    def test_grade_updates_schedule(self):
        r = self.client.post(f'/api/v1/reviews/{self.bite.id}/grade/', {'grade': 'good'}, format='json')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data['grade'], 'good')
        self.state.refresh_from_db()
        self.assertGreater(self.state.interval_days, 1)
        self.assertGreater(self.state.next_review_at, timezone.now())

    def test_grade_404_for_other_users_bite(self):
        other = _user('20002002')
        bite2 = Bite.objects.create(topic=self.topic, name='B2', bite='t')
        BiteReviewState.objects.create(
            account=other,
            bite=bite2,
            interval_days=1,
            repetitions=0,
            next_review_at=timezone.now() - timedelta(hours=1),
        )
        r = self.client.post(f'/api/v1/reviews/{bite2.id}/grade/', {'grade': 'good'}, format='json')
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)


class SubjectWeeklyGoalAPITests(TestCase):
    def setUp(self):
        self.user = _user('20003001')
        self.token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        self.subject = Subject.objects.create_subject_by_user(name='Gsub', description='d')
        Enrollment.objects.create(account=self.user, subject=self.subject)

    def test_create_and_list_goal(self):
        r = self.client.post(
            '/api/v1/subject-goals/',
            {'subject': self.subject.id, 'weekly_bite_target': 7, 'active': True},
            format='json',
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        r2 = self.client.get('/api/v1/subject-goals/')
        self.assertEqual(r2.status_code, status.HTTP_200_OK)
        self.assertEqual(len(r2.data), 1)
        self.assertEqual(r2.data[0]['weekly_bite_target'], 7)

    def test_duplicate_goal_rejected(self):
        SubjectWeeklyGoal.objects.create(
            account=self.user,
            subject=self.subject,
            weekly_bite_target=5,
            active=True,
        )
        r = self.client.post(
            '/api/v1/subject-goals/',
            {'subject': self.subject.id, 'weekly_bite_target': 3, 'active': True},
            format='json',
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_weekly_progress_endpoint(self):
        r = self.client.get(f'/api/v1/reviews/weekly-progress/{self.subject.id}/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIn('completed_this_week', r.data)
        self.assertEqual(r.data['subject_id'], self.subject.id)
