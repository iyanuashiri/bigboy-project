from unittest.mock import MagicMock, patch

from django.test import TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from bigboy.accounts.models import Account
from bigboy.subjects.models import Bite, Enrollment, Subject, Topic


def _user(suffix: str) -> Account:
    return Account.objects.create_user(
        phone_number=f'+234800{suffix}',
        password='test-pass-123',
        first_name='Sub',
        last_name='Test',
    )


class TopicRegenerateBitesTests(TestCase):
    def setUp(self):
        self.user = _user('50005001')
        self.token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        self.subject = Subject.objects.create_subject_by_user(name='RS', description='d')
        Enrollment.objects.create(account=self.user, subject=self.subject)
        self.topic = Topic.objects.create(
            subject=self.subject,
            name='RT',
            description='d',
            content='Topic body for generation.',
        )
        Bite.objects.create(topic=self.topic, name='keep', bite='locked content', is_locked=True)
        Bite.objects.create(topic=self.topic, name='drop', bite='unlocked content', is_locked=False)

    @patch('bigboy.subjects.models.generate_bites')
    def test_regenerate_removes_unlocked_and_calls_llm(self, mock_gen):
        nb = MagicMock()
        nb.title = 'New'
        nb.content = 'Generated bite text.'
        mock_gen.return_value = MagicMock(bites=[nb])

        r = self.client.post(f'/api/v1/topics/{self.topic.id}/regenerate-bites/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data['new_bite_count'], 1)
        names = list(self.topic.topic_bites.order_by('id').values_list('name', 'is_locked'))
        self.assertTrue(any(name == 'keep' and locked for name, locked in names))
        self.assertTrue(any(name == 'New' for name, _ in names))
        self.assertFalse(self.topic.topic_bites.filter(name='drop').exists())


class BitePatchAPITests(TestCase):
    def setUp(self):
        self.user = _user('50005002')
        self.token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        self.subject = Subject.objects.create_subject_by_user(name='PS', description='d')
        Enrollment.objects.create(account=self.user, subject=self.subject)
        self.topic = Topic.objects.create(
            subject=self.subject,
            name='PT',
            description='d',
            content='c',
        )
        self.bite = Bite.objects.create(topic=self.topic, name='n', bite='b')

    def test_patch_name_and_lock(self):
        r = self.client.patch(
            f'/api/v1/bites/{self.bite.id}/',
            {'name': 'Updated', 'bite': 'new body', 'is_locked': True},
            format='json',
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.bite.refresh_from_db()
        self.assertEqual(self.bite.name, 'Updated')
        self.assertEqual(self.bite.bite, 'new body')
        self.assertTrue(self.bite.is_locked)
