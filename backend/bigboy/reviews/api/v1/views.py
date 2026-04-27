import logging

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from bigboy.reviews.api.v1.serializers import (
    ReviewDueSerializer,
    ReviewGradeSerializer,
    SubjectWeeklyGoalReadSerializer,
    SubjectWeeklyGoalSerializer,
)
from bigboy.reviews.models import BiteReviewState, SubjectWeeklyGoal
from bigboy.reviews.services.goals import bites_completed_this_week
from bigboy.reviews.services.scheduling import apply_grade
from bigboy.subjects.api.v1.scoping import is_enrolled
from bigboy.subjects.models import Subject

logger = logging.getLogger(__name__)


class ReviewDueListView(generics.ListAPIView):
    """Bites that are due or overdue for spaced review."""

    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ReviewDueSerializer

    def get_queryset(self):
        now = timezone.now()
        return (
            BiteReviewState.objects.filter(account=self.request.user, next_review_at__lte=now)
            .select_related('bite__topic__subject')
            .order_by('next_review_at', 'id')
        )


class ReviewGradeView(APIView):
    """Submit a review grade (again / hard / good / easy) for a scheduled bite."""

    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, bite_id):
        serializer = ReviewGradeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        grade = serializer.validated_data['grade']

        state = get_object_or_404(
            BiteReviewState.objects.select_related('bite__topic__subject'),
            account=request.user,
            bite_id=bite_id,
        )
        subject_id = state.bite.topic.subject_id
        if not is_enrolled(request.user, subject_id):
            return Response({'detail': 'Not enrolled.'}, status=status.HTTP_403_FORBIDDEN)

        new_interval, new_rep, delta = apply_grade(
            grade=grade,
            interval_days=state.interval_days,
            repetitions=state.repetitions,
        )
        now = timezone.now()
        state.interval_days = new_interval
        state.repetitions = new_rep
        state.last_grade = grade
        state.last_reviewed_at = now
        state.next_review_at = now + delta
        state.save(
            update_fields=[
                'interval_days',
                'repetitions',
                'last_grade',
                'last_reviewed_at',
                'next_review_at',
                'updated_at',
            ],
        )
        return Response(
            {
                'bite_id': bite_id,
                'grade': grade,
                'next_review_at': state.next_review_at,
                'interval_days': state.interval_days,
                'repetitions': state.repetitions,
            },
            status=status.HTTP_200_OK,
        )


class SubjectWeeklyGoalListCreateView(generics.ListCreateAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return SubjectWeeklyGoal.objects.filter(account=self.request.user).select_related('subject')

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return SubjectWeeklyGoalReadSerializer
        return SubjectWeeklyGoalSerializer

    def perform_create(self, serializer):
        serializer.save(account=self.request.user)


class SubjectWeeklyGoalDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return SubjectWeeklyGoal.objects.filter(account=self.request.user).select_related('subject')

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return SubjectWeeklyGoalReadSerializer
        return SubjectWeeklyGoalSerializer


class SubjectGoalProgressView(APIView):
    """Convenience: weekly bite completions vs optional goal for one subject."""

    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, subject_id):
        if not is_enrolled(request.user, subject_id):
            return Response({'detail': 'Not enrolled in this subject.'}, status=status.HTTP_403_FORBIDDEN)
        get_object_or_404(Subject, pk=subject_id)
        done = bites_completed_this_week(account=request.user, subject_id=subject_id)
        goal = SubjectWeeklyGoal.objects.filter(
            account=request.user,
            subject_id=subject_id,
            active=True,
        ).first()
        target = goal.weekly_bite_target if goal else None
        return Response(
            {
                'subject_id': subject_id,
                'completed_this_week': done,
                'weekly_bite_target': target,
                'goal_active': bool(goal and goal.active),
            },
        )
