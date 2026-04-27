from django.test import TestCase

from bigboy.accounts.models import Account
from bigboy.quizzes.api.v1.serializers import QuizReadSerializer
from bigboy.quizzes.models import Option, Question, Quiz
from bigboy.subjects.models import Enrollment, Subject, Topic


def _user(suffix: str) -> Account:
    return Account.objects.create_user(
        phone_number=f'+234800{suffix}',
        password='test-pass-123',
        first_name='Qz',
        last_name='Test',
    )


class QuizReadSerializerShuffleTests(TestCase):
    def setUp(self):
        self.user = _user('60006001')
        self.subject = Subject.objects.create_subject_by_user(name='QS', description='d')
        Enrollment.objects.create(account=self.user, subject=self.subject)
        self.topic = Topic.objects.create(
            subject=self.subject,
            name='QT',
            description='d',
            content='c',
        )
        self.quiz = Quiz.objects.create(
            subject=self.subject,
            topic=self.topic,
            number_of_questions=1,
            number_of_options=4,
        )
        self.q = Question.objects.create(quiz=self.quiz, question='Q1?')
        self.opt_ids = []
        for i, letter in enumerate(['A', 'B', 'C', 'D']):
            self.opt_ids.append(
                Option.objects.create(
                    question=self.q,
                    option=letter,
                    is_correct=(letter == 'B'),
                ).id,
            )

    def test_to_representation_shuffles_option_order(self):
        ser = QuizReadSerializer()
        data = ser.to_representation(self.quiz)
        q0 = data['quiz_questions'][0]
        order_first = [o['id'] for o in q0['question_options']]
        seen = {tuple(order_first)}
        for _ in range(25):
            data = ser.to_representation(self.quiz)
            order = [o['id'] for o in data['quiz_questions'][0]['question_options']]
            seen.add(tuple(order))
        self.assertGreater(len(seen), 1, 'shuffle should vary option order across reads')
