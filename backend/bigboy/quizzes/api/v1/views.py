import logging

from rest_framework import generics, permissions, status
from rest_framework.response import Response

from bigboy.accounts.models import Point
from bigboy.quizzes.models import Answer, Quiz
from bigboy.quizzes.services.explain_wrong import explain_wrong_answer
from bigboy.quizzes.api.v1.serializers import (
    QuizAnswerSubmitSerializer,
    QuizReadSerializer,
    QuizSerializer,
)

logger = logging.getLogger(__name__)


class QuizListCreateView(generics.ListCreateAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        qs = Quiz.objects.filter(
            subject_id__in=user.account_enrollments.values_list('subject_id', flat=True),
        ).select_related('subject', 'topic').order_by('id')
        subject_id = self.request.query_params.get('subject')
        if subject_id is not None:
            try:
                sid = int(subject_id)
            except (TypeError, ValueError):
                return Quiz.objects.none()
            if not user.account_enrollments.filter(subject_id=sid).exists():
                return Quiz.objects.none()
            qs = qs.filter(subject_id=sid)
        return qs

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return QuizReadSerializer
        return QuizSerializer


class QuizRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        return Quiz.objects.filter(
            subject_id__in=user.account_enrollments.values_list('subject_id', flat=True),
        ).select_related('subject', 'topic')

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return QuizReadSerializer
        return QuizSerializer


class QuizAnswerSubmitView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = QuizAnswerSubmitSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        question = serializer.validated_data['question']
        option = serializer.validated_data['selected_option']
        account = request.user
        quiz = question.quiz

        Answer.objects.create(
            account=account,
            question=question,
            selected_option=option,
        )

        why_wrong = None
        if option.is_correct:
            point_record = Point.objects.award_question_answered_correctly(account=account)
        else:
            point_record = Point.objects.award_question_answered_incorrectly(account=account)
            try:
                correct_opt = question.question_options.filter(is_correct=True).first()
                why_wrong = explain_wrong_answer(
                    question_text=question.question,
                    chosen_option=option.option,
                    correct_option=correct_opt.option if correct_opt else '',
                    topic_excerpt=(quiz.topic.content or '')[:4000],
                )
            except Exception:
                logger.exception('why_wrong generation failed question_id=%s', question.id)
        total_q = quiz.quiz_questions.count()
        answered_q = Answer.objects.filter(account=account, question__quiz=quiz).count()
        quiz_completed = False
        completion_record = None
        if total_q > 0 and answered_q >= total_q:
            completion_record = Point.objects.award_quiz_completed(account=account)
            quiz_completed = True

        account.refresh_from_db()

        return Response(
            {
                'is_correct': option.is_correct,
                'question_id': question.id,
                'points_earned': point_record.point if point_record else 0,
                'total_points': account.total_points,
                'quiz_id': quiz.id,
                'quiz_completed': quiz_completed,
                'quiz_completion_points': completion_record.point if completion_record else 0,
                'why_wrong': why_wrong,
            },
            status=status.HTTP_201_CREATED,
        )
