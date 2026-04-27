from django.contrib import admin

from bigboy.sources import models as source_models


@admin.register(source_models.DocumentCategory)
class DocumentCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'account', 'created_at')
    search_fields = ('name', 'account__phone_number')
    raw_id_fields = ('account',)


@admin.register(source_models.SourceDocument)
class SourceDocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'original_name', 'category', 'status', 'created_at')
    list_filter = ('status',)
    raw_id_fields = ('category',)


@admin.register(source_models.DocumentChatSession)
class DocumentChatSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'category', 'title', 'created_at')
    raw_id_fields = ('category',)


@admin.register(source_models.DocumentChatMessage)
class DocumentChatMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'role', 'created_at')
    list_filter = ('role',)
    raw_id_fields = ('session',)


@admin.register(source_models.ResearchRun)
class ResearchRunAdmin(admin.ModelAdmin):
    list_display = ('id', 'account', 'status', 'created_at', 'completed_at')
    list_filter = ('status',)
    search_fields = ('query', 'graph_run_id')
    raw_id_fields = ('account',)


@admin.register(source_models.McpConversationImport)
class McpConversationImportAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'account', 'client_label', 'status', 'created_at')
    list_filter = ('status',)
    raw_id_fields = ('account',)


@admin.register(source_models.SourcePromotion)
class SourcePromotionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'account',
        'source_content_type',
        'source_object_id',
        'target_content_type',
        'target_object_id',
        'status',
        'created_at',
    )
    list_filter = ('status', 'source_content_type', 'target_content_type')
    raw_id_fields = ('account', 'source_content_type', 'target_content_type')
