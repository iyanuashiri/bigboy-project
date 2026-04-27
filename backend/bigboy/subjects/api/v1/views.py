import logging

from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from bigboy.subjects.api.v1.serializers import (
    BiteUpdateSerializer,
    EnrollmentReadSerializer,
    EnrollmentSerializer,
    SubjectCatalogSerializer,
    SubjectReadSerializer,
    SubjectSerializer,
    TopicReadSerializer,
    TopicSerializer,
)
from bigboy.subjects.api.v1.scoping import is_enrolled, subjects_queryset_for_user
from bigboy.subjects.models import Bite, Enrollment, Subject, Topic
from bigboy.subjects.services.lesson_progress import build_subject_progress, complete_bite_for_user

logger = logging.getLogger(__name__)


class SubjectListCreateView(generics.ListCreateAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        if self.request.method != 'GET':
            return Subject.objects.all().order_by('id')
        scope = self.request.query_params.get('scope', 'enrolled')
        if scope not in ('enrolled', 'catalog'):
            scope = 'enrolled'
        return subjects_queryset_for_user(self.request.user, scope)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            scope = self.request.query_params.get('scope', 'enrolled')
            if scope == 'catalog':
                return SubjectCatalogSerializer
            return SubjectReadSerializer
        return SubjectSerializer


class SubjectRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return (
            Subject.objects.filter(
                subject_enrollments__account=self.request.user,
            )
            .distinct()
            .prefetch_related(
                'subject_topics__topic_bites',
                'subject_topics__topic_quizzes',
            )
        )

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return SubjectReadSerializer
        return SubjectSerializer


class TopicListCreateView(generics.ListCreateAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        if self.request.method == 'GET':
            subject_id = self.request.query_params.get('subject')
            if not subject_id:
                return Topic.objects.none()
            try:
                sid = int(subject_id)
            except (TypeError, ValueError):
                return Topic.objects.none()
            if not is_enrolled(user, sid):
                return Topic.objects.none()
            return Topic.objects.filter(subject_id=sid).order_by('id')
        return Topic.objects.filter(
            subject__subject_enrollments__account=user,
        ).distinct()

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return TopicReadSerializer
        return TopicSerializer

    def list(self, request, *args, **kwargs):
        if request.method == 'GET' and not request.query_params.get('subject'):
            return Response(
                {'detail': 'Query parameter "subject" is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if request.method == 'GET':
            try:
                sid = int(request.query_params.get('subject'))
            except (TypeError, ValueError):
                return Response(
                    {'detail': 'Invalid "subject" query parameter.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not is_enrolled(request.user, sid):
                return Response(
                    {'detail': 'You are not enrolled in this subject.'},
                    status=status.HTTP_403_FORBIDDEN,
                )
        return super().list(request, *args, **kwargs)

    def perform_create(self, serializer):
        subject = serializer.validated_data['subject']
        if not is_enrolled(self.request.user, subject.id):
            raise PermissionDenied('You must be enrolled in this subject to create topics.')
        serializer.save()


class TopicRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return (
            Topic.objects.filter(
                subject__subject_enrollments__account=self.request.user,
            )
            .select_related('subject')
            .prefetch_related('topic_bites')
            .distinct()
        )

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return TopicReadSerializer
        return TopicSerializer


class EnrollmentListCreateView(generics.ListCreateAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Enrollment.objects.filter(account=self.request.user).order_by('-date_enrolled')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return EnrollmentSerializer
        return EnrollmentReadSerializer

    def perform_create(self, serializer):
        try:
            serializer.save(account=self.request.user)
        except IntegrityError:
            raise ValidationError({'subject': 'Already enrolled in this subject.'})


class EnrollmentDestroyView(generics.DestroyAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = EnrollmentReadSerializer

    def get_queryset(self):
        return Enrollment.objects.filter(account=self.request.user)


class SubjectProgressView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, subject_id):
        if not is_enrolled(request.user, subject_id):
            return Response({'detail': 'Not enrolled in this subject.'}, status=status.HTTP_403_FORBIDDEN)
        subject = get_object_or_404(Subject, pk=subject_id)
        return Response(build_subject_progress(request.user, subject))


class TopicRegenerateBitesView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, pk):
        topic = get_object_or_404(
            Topic.objects.filter(
                subject__subject_enrollments__account=request.user,
            ).distinct(),
            pk=pk,
        )
        try:
            created = topic.regenerate_bites()
        except Exception:
            logger.exception('regenerate_bites failed for topic_id=%s', pk)
            return Response(
                {'detail': 'Could not regenerate bites. Check server logs and Bedrock configuration.'},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        return Response({'new_bite_count': created}, status=status.HTTP_200_OK)


class BiteRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = BiteUpdateSerializer
    http_method_names = ['get', 'patch', 'head', 'options']

    def get_queryset(self):
        return (
            Bite.objects.filter(
                topic__subject__subject_enrollments__account=self.request.user,
            )
            .select_related('topic__subject')
            .distinct()
        )


class BiteCompleteView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, bite_id):
        try:
            data = complete_bite_for_user(request.user, bite_id)
        except Bite.DoesNotExist:
            return Response({'detail': 'Bite not found.'}, status=status.HTTP_404_NOT_FOUND)
        except PermissionError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_403_FORBIDDEN)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(data, status=status.HTTP_200_OK)
