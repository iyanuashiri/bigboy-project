from unittest.mock import patch

from django.test import TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from bigboy.accounts.models import Account
from bigboy.quizzes.models import Answer, Option, Question, Quiz
from bigboy.subjects.models import Enrollment, Subject, Topic


def _user(suffix: str) -> Account:
    return Account.objects.create_user(
        phone_number=f'+234800{suffix}',
        password='test-pass-123',
        first_name='Ans',
        last_name='Test',
    )


class QuizAnswerWhyWrongTests(TestCase):
    def setUp(self):
        self.user = _user('60007001')
        self.token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        self.subject = Subject.objects.create_subject_by_user(name='AS', description='d')
        Enrollment.objects.create(account=self.user, subject=self.subject)
        self.topic = Topic.objects.create(
            subject=self.subject,
            name='AT',
            description='d',
            content='The capital of France is Paris.',
        )
        self.quiz = Quiz.objects.create(
            subject=self.subject,
            topic=self.topic,
            number_of_questions=1,
            number_of_options=2,
        )
        self.question = Question.objects.create(quiz=self.quiz, question='Capital of France?')
        self.wrong = Option.objects.create(question=self.question, option='Berlin', is_correct=False)
        self.right = Option.objects.create(question=self.question, option='Paris', is_correct=True)

    @patch('bigboy.quizzes.api.v1.views.explain_wrong_answer')
    def test_why_wrong_on_incorrect(self, mock_explain):
        mock_explain.return_value = 'Paris is the capital, not Berlin.'
        r = self.client.post(
            '/api/v1/quiz-answers/',
            {'question': self.question.id, 'selected_option': self.wrong.id},
            format='json',
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertFalse(r.data['is_correct'])
        self.assertEqual(r.data['why_wrong'], 'Paris is the capital, not Berlin.')
        mock_explain.assert_called_once()

    def test_no_why_when_correct(self):
        r = self.client.post(
            '/api/v1/quiz-answers/',
            {'question': self.question.id, 'selected_option': self.right.id},
            format='json',
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertTrue(r.data['is_correct'])
        self.assertIsNone(r.data.get('why_wrong'))

    def test_cannot_answer_same_question_twice(self):
        self.client.post(
            '/api/v1/quiz-answers/',
            {'question': self.question.id, 'selected_option': self.right.id},
            format='json',
        )
        r = self.client.post(
            '/api/v1/quiz-answers/',
            {'question': self.question.id, 'selected_option': self.right.id},
            format='json',
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Answer.objects.filter(account=self.user, question=self.question).count(), 1)
