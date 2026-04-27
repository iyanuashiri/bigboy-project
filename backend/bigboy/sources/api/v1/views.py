import hashlib
import logging
import uuid

from django.conf import settings as django_settings
from django.core.files.storage import default_storage
from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from bigboy.sources.models import (
    DocumentCategory,
    DocumentChatMessage,
    DocumentChatSession,
    McpConversationImport,
    ResearchRun,
    SourceDocument,
    SourcePromotion,
)
from bigboy.sources.api.v1.serializers import (
    DocumentCategoryListSerializer,
    DocumentCategorySerializer,
    DocumentCategoryWriteSerializer,
    DocumentChatMessageSerializer,
    DocumentChatMessageWriteSerializer,
    DocumentChatSessionSerializer,
    DocumentChatSessionWriteSerializer,
    McpConversationImportSerializer,
    McpConversationImportWriteSerializer,
    PromoteToSubjectSerializer,
    ResearchRunSerializer,
    SourceDocumentSerializer,
    SourceDocumentWriteSerializer,
    SourcePromotionSerializer,
)
from bigboy.sources.services.langgraph_research import invoke_research_agent
from bigboy.sources.services.promotion import promote_to_subject
from bigboy.sources.services.rag import index_source_document, rag_reply_for_session

logger = logging.getLogger(__name__)


class DocumentCategoryListCreateView(generics.ListCreateAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return (
            DocumentCategory.objects.filter(account=self.request.user)
            .annotate(document_count=Count('documents'))
            .order_by('-created_at')
        )

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return DocumentCategoryListSerializer
        return DocumentCategoryWriteSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        name_in = (data.get('name') or '').strip()
        description = (data.get('description') or '').strip()
        if name_in:
            obj = DocumentCategory.objects.create(
                account=request.user,
                name=name_in[:200],
                description=description,
                auto_label_completed=True,
            )
        else:
            obj = DocumentCategory.objects.create(
                account=request.user,
                name='Documents',
                description=description,
                auto_label_completed=False,
            )
        return Response(
            DocumentCategorySerializer(obj).data,
            status=status.HTTP_201_CREATED,
        )


class DocumentCategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = DocumentCategorySerializer

    def get_queryset(self):
        return DocumentCategory.objects.filter(account=self.request.user).prefetch_related('documents')

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return DocumentCategoryWriteSerializer
        return DocumentCategorySerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = DocumentCategoryWriteSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        instance.refresh_from_db()
        return Response(DocumentCategorySerializer(instance).data)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)


class SourceDocumentListCreateView(generics.ListCreateAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get_category(self):
        return get_object_or_404(
            DocumentCategory,
            pk=self.kwargs['pk'],
            account=self.request.user,
        )

    def get_queryset(self):
        return SourceDocument.objects.filter(category=self.get_category()).order_by('id')

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return SourceDocumentSerializer
        return SourceDocumentWriteSerializer

    def perform_create(self, serializer):
        serializer.save(category=self.get_category())

    def create(self, request, *args, **kwargs):
        category = self.get_category()
        upload = request.FILES.get('file')
        if upload:
            raw = upload.read()
            digest = hashlib.sha256(raw).hexdigest()
            upload.seek(0)
            rel = f'source_documents/{request.user.id}/{uuid.uuid4().hex}_{upload.name}'
            path = default_storage.save(rel, upload)
            name = (request.data.get('original_name') or upload.name or 'document')[:255]
            mime = getattr(upload, 'content_type', '') or ''
            doc = SourceDocument.objects.create(
                category=category,
                original_name=name,
                stored_path=path,
                mime_type=mime[:120],
                size_bytes=len(raw),
                sha256=digest,
                status=SourceDocument.ProcessingStatus.UPLOADED,
            )
            try:
                index_source_document(doc)
            except Exception as exc:  # noqa: BLE001
                logger.exception('Document indexing failed')
                doc.status = SourceDocument.ProcessingStatus.FAILED
                doc.processing_error = str(exc)[:2000]
                doc.save(update_fields=['status', 'processing_error', 'updated_at'])
            doc.refresh_from_db()
            return Response(SourceDocumentSerializer(doc).data, status=status.HTTP_201_CREATED)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SourceDocumentDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = SourceDocumentSerializer

    def get_queryset(self):
        return SourceDocument.objects.filter(category__account=self.request.user)

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return SourceDocumentWriteSerializer
        return SourceDocumentSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = SourceDocumentWriteSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        instance.refresh_from_db()
        return Response(SourceDocumentSerializer(instance).data)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)


class DocumentChatSessionListCreateView(generics.ListCreateAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get_category(self):
        return get_object_or_404(
            DocumentCategory,
            pk=self.kwargs['pk'],
            account=self.request.user,
        )

    def get_queryset(self):
        return DocumentChatSession.objects.filter(category=self.get_category()).prefetch_related('messages')

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return DocumentChatSessionSerializer
        return DocumentChatSessionWriteSerializer

    def perform_create(self, serializer):
        serializer.save(category=self.get_category())

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        obj = DocumentChatSession.objects.create(
            category=self.get_category(),
            **serializer.validated_data,
        )
        return Response(
            DocumentChatSessionSerializer(obj).data,
            status=status.HTTP_201_CREATED,
        )


class DocumentChatSessionDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return DocumentChatSession.objects.filter(category__account=self.request.user).prefetch_related('messages')

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return DocumentChatSessionWriteSerializer
        return DocumentChatSessionSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = DocumentChatSessionWriteSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        instance.refresh_from_db()
        return Response(DocumentChatSessionSerializer(instance).data)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)


class DocumentChatMessageListCreateView(generics.ListCreateAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get_session(self):
        return get_object_or_404(
            DocumentChatSession,
            pk=self.kwargs['pk'],
            category__account=self.request.user,
        )

    def get_queryset(self):
        return DocumentChatMessage.objects.filter(session=self.get_session()).order_by('created_at', 'id')

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return DocumentChatMessageSerializer
        return DocumentChatMessageWriteSerializer

    def perform_create(self, serializer):
        serializer.save(session=self.get_session())

    def create(self, request, *args, **kwargs):
        session = self.get_session()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        role = serializer.validated_data.get('role')
        if role != DocumentChatMessage.Role.USER:
            return Response(
                {'detail': 'Only role "user" is supported. The assistant reply is generated by the server.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user_msg = serializer.save(session=session)
        try:
            assistant_text, meta = rag_reply_for_session(session=session, user_message=user_msg)
        except Exception as exc:  # noqa: BLE001
            logger.exception('RAG reply failed')
            assistant_text = (
                f'I could not generate an answer from your documents ({type(exc).__name__}: {exc}). '
                'Check AWS credentials and that documents are indexed.'
            )
            meta = {'rag': True, 'error': True}
        assistant = DocumentChatMessage.objects.create(
            session=session,
            role=DocumentChatMessage.Role.ASSISTANT,
            content=assistant_text,
            metadata=meta,
        )
        return Response(
            {
                'user_message': DocumentChatMessageSerializer(user_msg).data,
                'assistant_message': DocumentChatMessageSerializer(assistant).data,
            },
            status=status.HTTP_201_CREATED,
        )


class ResearchRunListCreateView(generics.ListCreateAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ResearchRunSerializer

    def get_queryset(self):
        return ResearchRun.objects.filter(account=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        instance = serializer.save()
        now = timezone.now()
        if not (django_settings.LANGGRAPH_SERVICE_URL or '').strip():
            ResearchRun.objects.filter(pk=instance.pk).update(
                status=ResearchRun.Status.FAILED,
                error_message=(
                    'LANGGRAPH_SERVICE_URL is not set on the Django server. '
                    'Example: LANGGRAPH_SERVICE_URL=http://127.0.0.1:8765'
                )[:10000],
                completed_at=now,
            )
            instance.refresh_from_db()
            return

        ResearchRun.objects.filter(pk=instance.pk).update(status=ResearchRun.Status.RUNNING)
        instance.refresh_from_db()

        outcome = invoke_research_agent(
            query=instance.query,
            thread_id=str(instance.pk),
        )

        now = timezone.now()
        if outcome.get('ok'):
            ResearchRun.objects.filter(pk=instance.pk).update(
                status=ResearchRun.Status.SUCCEEDED,
                graph_run_id=(outcome.get('thread_id') or '')[:120],
                result_blocks=outcome.get('result_blocks') or [],
                error_message='',
                completed_at=now,
            )
        else:
            ResearchRun.objects.filter(pk=instance.pk).update(
                status=ResearchRun.Status.FAILED,
                graph_run_id=(outcome.get('thread_id') or '')[:120],
                result_blocks=outcome.get('result_blocks') or [],
                error_message=(outcome.get('error_message') or 'Research agent run failed.')[:10000],
                completed_at=now,
            )
        instance.refresh_from_db()


class ResearchRunDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ResearchRunSerializer

    def get_queryset(self):
        return ResearchRun.objects.filter(account=self.request.user)


class McpConversationImportListCreateView(generics.ListCreateAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return McpConversationImport.objects.filter(account=self.request.user).order_by('-created_at')

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return McpConversationImportSerializer
        return McpConversationImportWriteSerializer

    def perform_create(self, serializer):
        extra = {}
        if not serializer.validated_data.get('transcript'):
            extra['transcript'] = '(No transcript text was included with this import.)'
        serializer.save(account=self.request.user, **extra)


class McpConversationImportDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return McpConversationImport.objects.filter(account=self.request.user)

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return McpConversationImportWriteSerializer
        return McpConversationImportSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = McpConversationImportWriteSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        instance.refresh_from_db()
        return Response(McpConversationImportSerializer(instance).data)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)


class SourcePromotionListView(generics.ListAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = SourcePromotionSerializer

    def get_queryset(self):
        return SourcePromotion.objects.filter(account=self.request.user).order_by('-created_at')


class PromoteToSubjectView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        serializer = PromoteToSubjectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        subject, promotion, err = promote_to_subject(
            account=request.user,
            source_model_slug=serializer.validated_data['source_model'],
            source_id=serializer.validated_data['source_id'],
            subject_name=serializer.validated_data['subject_name'],
            subject_description=serializer.validated_data['subject_description'],
        )
        if err:
            return Response({'detail': err}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            {
                'subject_id': subject.id,
                'promotion_id': promotion.id,
            },
            status=status.HTTP_201_CREATED,
        )
