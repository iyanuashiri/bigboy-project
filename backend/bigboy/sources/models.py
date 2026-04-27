from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class DocumentCategory(models.Model):
    """User-defined bucket of documents for RAG-style chat (Explore → Documents)."""

    account = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='document_categories',
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    auto_label_completed = models.BooleanField(
        default=False,
        help_text='When true, name/description were finalized (or user had a pre-migration category).',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['account', '-created_at']),
        ]

    def __str__(self):
        return f'{self.name} ({self.account_id})'


class SourceDocument(models.Model):
    """Single file (or stored object) belonging to a document category."""

    class ProcessingStatus(models.TextChoices):
        UPLOADED = 'uploaded', 'Uploaded'
        PROCESSING = 'processing', 'Processing'
        INDEXED = 'indexed', 'Indexed'
        FAILED = 'failed', 'Failed'

    category = models.ForeignKey(
        DocumentCategory,
        on_delete=models.CASCADE,
        related_name='documents',
    )
    original_name = models.CharField(max_length=255)
    stored_path = models.CharField(
        max_length=500,
        blank=True,
        help_text='Storage path or object key after upload (S3, local, etc.).',
    )
    mime_type = models.CharField(max_length=120, blank=True)
    size_bytes = models.BigIntegerField(null=True, blank=True)
    sha256 = models.CharField(max_length=64, blank=True)
    status = models.CharField(
        max_length=20,
        choices=ProcessingStatus.choices,
        default=ProcessingStatus.UPLOADED,
    )
    processing_error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'id']
        indexes = [
            models.Index(fields=['category', 'status']),
        ]

    def __str__(self):
        return self.original_name


class DocumentChunk(models.Model):
    """Text segment + embedding for RAG over a source document."""

    source_document = models.ForeignKey(
        SourceDocument,
        on_delete=models.CASCADE,
        related_name='chunks',
    )
    chunk_index = models.PositiveIntegerField()
    text = models.TextField()
    embedding = models.JSONField(default=list, help_text='Dense vector from Bedrock embeddings (list of floats).')

    class Meta:
        ordering = ['source_document_id', 'chunk_index']
        constraints = [
            models.UniqueConstraint(
                fields=('source_document', 'chunk_index'),
                name='sources_documentchunk_source_document_chunk_index_uniq',
            ),
        ]
        indexes = [
            models.Index(fields=['source_document', 'chunk_index']),
        ]

    def __str__(self):
        return f'chunk {self.chunk_index} of {self.source_document_id}'


class DocumentChatSession(models.Model):
    """Chat thread scoped to one document category (RAG context = that category's corpus)."""

    category = models.ForeignKey(
        DocumentCategory,
        on_delete=models.CASCADE,
        related_name='chat_sessions',
    )
    title = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title or f'Session {self.pk}'


class DocumentChatMessage(models.Model):
    """One turn in a document-grounded chat."""

    class Role(models.TextChoices):
        USER = 'user', 'User'
        ASSISTANT = 'assistant', 'Assistant'
        SYSTEM = 'system', 'System'

    session = models.ForeignKey(
        DocumentChatSession,
        on_delete=models.CASCADE,
        related_name='messages',
    )
    role = models.CharField(max_length=20, choices=Role.choices)
    content = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at', 'id']

    def __str__(self):
        return f'{self.role} @ {self.session_id}'


class ResearchRun(models.Model):
    """One LangGraph (or similar) research job from a natural-language brief."""

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        QUEUED = 'queued', 'Queued'
        RUNNING = 'running', 'Running'
        SUCCEEDED = 'succeeded', 'Succeeded'
        FAILED = 'failed', 'Failed'

    account = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='research_runs',
    )
    query = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    result_blocks = models.JSONField(
        default=list,
        blank=True,
        help_text='Structured sections, e.g. list of {title, body} until normalized.',
    )
    graph_run_id = models.CharField(
        max_length=120,
        blank=True,
        help_text='External orchestrator / LangGraph run reference.',
    )
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['account', '-created_at']),
            models.Index(fields=['account', 'status']),
        ]

    def __str__(self):
        return f'Research {self.pk}: {self.query[:40]}'


class McpConversationImport(models.Model):
    """One conversation snapshot imported via MCP (any client)."""

    class Status(models.TextChoices):
        RECEIVED = 'received', 'Received'
        PARSED = 'parsed', 'Parsed'
        FAILED = 'failed', 'Failed'

    account = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mcp_conversation_imports',
    )
    title = models.CharField(max_length=255)
    client_label = models.CharField(
        max_length=120,
        blank=True,
        help_text='Which MCP host/client produced this import, if known.',
    )
    raw_payload = models.JSONField(
        default=dict,
        blank=True,
        help_text='Raw MCP / tool payload for auditing and re-processing.',
    )
    transcript = models.TextField(
        blank=True,
        help_text='Flattened or human-readable conversation text for UI and search.',
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.RECEIVED,
    )
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['account', '-created_at']),
        ]

    def __str__(self):
        return self.title


class SourcePromotion(models.Model):
    """
    Records conversion of a neutral source row into a curriculum (or other) artifact.

    ``source`` typically points at ``DocumentCategory``, ``ResearchRun``, or
    ``McpConversationImport``; ``target`` at ``subjects.Subject`` or future models.
    Validate allowed (app_label, model) pairs in your service layer.
    """

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'

    account = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='source_promotions',
    )
    source_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='+',
    )
    source_object_id = models.PositiveBigIntegerField()
    source = GenericForeignKey('source_content_type', 'source_object_id')

    target_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='+',
    )
    target_object_id = models.PositiveBigIntegerField()
    target = GenericForeignKey('target_content_type', 'target_object_id')

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    error_message = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['account', '-created_at']),
            models.Index(fields=['source_content_type', 'source_object_id']),
            models.Index(fields=['target_content_type', 'target_object_id']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=[
                    'source_content_type',
                    'source_object_id',
                    'target_content_type',
                    'target_object_id',
                ],
                name='sources_promotion_unique_source_target',
            ),
        ]

    def __str__(self):
        return f'Promotion {self.pk}: {self.source_content_type_id}/{self.source_object_id} → {self.target_content_type_id}/{self.target_object_id}'
