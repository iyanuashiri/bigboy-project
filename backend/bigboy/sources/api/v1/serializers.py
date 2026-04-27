from rest_framework import serializers

from bigboy.sources.models import (
    DocumentCategory,
    DocumentChatMessage,
    DocumentChatSession,
    McpConversationImport,
    ResearchRun,
    SourceDocument,
    SourcePromotion,
)


class SourceDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SourceDocument
        fields = (
            'id',
            'category',
            'original_name',
            'stored_path',
            'mime_type',
            'size_bytes',
            'sha256',
            'status',
            'processing_error',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'category', 'status', 'processing_error', 'created_at', 'updated_at')


class SourceDocumentWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = SourceDocument
        fields = (
            'original_name',
            'stored_path',
            'mime_type',
            'size_bytes',
            'sha256',
        )


class DocumentCategoryListSerializer(serializers.ModelSerializer):
    document_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = DocumentCategory
        fields = (
            'id',
            'name',
            'description',
            'auto_label_completed',
            'document_count',
            'created_at',
            'updated_at',
        )


class DocumentCategorySerializer(serializers.ModelSerializer):
    documents = SourceDocumentSerializer(many=True, read_only=True)

    class Meta:
        model = DocumentCategory
        fields = (
            'id',
            'name',
            'description',
            'auto_label_completed',
            'documents',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'auto_label_completed', 'documents', 'created_at', 'updated_at')


class DocumentCategoryWriteSerializer(serializers.ModelSerializer):
    """`name` is optional at create — the server uses a placeholder until the first document is indexed."""

    class Meta:
        model = DocumentCategory
        fields = ('name', 'description')
        extra_kwargs = {
            'name': {'required': False, 'allow_blank': True},
            'description': {'required': False, 'allow_blank': True},
        }


class DocumentChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentChatMessage
        fields = ('id', 'session', 'role', 'content', 'metadata', 'created_at')
        read_only_fields = ('id', 'session', 'created_at')


class DocumentChatMessageWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentChatMessage
        fields = ('role', 'content', 'metadata')


class DocumentChatSessionSerializer(serializers.ModelSerializer):
    messages = DocumentChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = DocumentChatSession
        fields = ('id', 'category', 'title', 'messages', 'created_at', 'updated_at')
        read_only_fields = ('id', 'category', 'messages', 'created_at', 'updated_at')


class DocumentChatSessionWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentChatSession
        fields = ('title',)


class ResearchRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResearchRun
        fields = (
            'id',
            'account',
            'query',
            'status',
            'result_blocks',
            'graph_run_id',
            'error_message',
            'created_at',
            'updated_at',
            'completed_at',
        )
        read_only_fields = ('id', 'account', 'created_at', 'updated_at')

    def create(self, validated_data):
        validated_data['account'] = self.context['request'].user
        for key in ('status', 'result_blocks', 'graph_run_id', 'error_message', 'completed_at'):
            validated_data.pop(key, None)
        validated_data['result_blocks'] = []
        validated_data['status'] = ResearchRun.Status.QUEUED
        return super().create(validated_data)


class McpConversationImportSerializer(serializers.ModelSerializer):
    lines = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = McpConversationImport
        fields = (
            'id',
            'title',
            'client_label',
            'raw_payload',
            'transcript',
            'lines',
            'status',
            'error_message',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'lines', 'created_at', 'updated_at')

    def get_lines(self, obj):
        if not obj.transcript:
            return []
        return [ln for ln in obj.transcript.splitlines() if ln.strip()]


class McpConversationImportWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = McpConversationImport
        fields = (
            'title',
            'client_label',
            'raw_payload',
            'transcript',
            'status',
            'error_message',
        )


class SourcePromotionSerializer(serializers.ModelSerializer):
    source_model = serializers.SerializerMethodField()
    target_model = serializers.SerializerMethodField()

    class Meta:
        model = SourcePromotion
        fields = (
            'id',
            'source_model',
            'source_object_id',
            'target_model',
            'target_object_id',
            'status',
            'error_message',
            'metadata',
            'created_at',
            'updated_at',
        )
        read_only_fields = fields

    def get_source_model(self, obj):
        return f'{obj.source_content_type.app_label}.{obj.source_content_type.model}'

    def get_target_model(self, obj):
        return f'{obj.target_content_type.app_label}.{obj.target_content_type.model}'


class PromoteToSubjectSerializer(serializers.Serializer):
    source_model = serializers.ChoiceField(
        choices=[
            ('documentcategory', 'Document category'),
            ('researchrun', 'Research run'),
            ('mcpconversationimport', 'MCP import'),
        ],
    )
    source_id = serializers.IntegerField(min_value=1)
    subject_name = serializers.CharField(max_length=100)
    subject_description = serializers.CharField()
