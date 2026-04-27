from django.urls import path

from . import views

app_name = 'sources'

urlpatterns = [
    path('document-categories/<int:pk>/documents/', views.SourceDocumentListCreateView.as_view()),
    path('document-categories/<int:pk>/chat-sessions/', views.DocumentChatSessionListCreateView.as_view()),
    path('document-categories/<int:pk>/', views.DocumentCategoryDetailView.as_view()),
    path('document-categories/', views.DocumentCategoryListCreateView.as_view()),
    path('source-documents/<int:pk>/', views.SourceDocumentDetailView.as_view()),
    path('chat-sessions/<int:pk>/messages/', views.DocumentChatMessageListCreateView.as_view()),
    path('chat-sessions/<int:pk>/', views.DocumentChatSessionDetailView.as_view()),
    path('research-runs/<int:pk>/', views.ResearchRunDetailView.as_view()),
    path('research-runs/', views.ResearchRunListCreateView.as_view()),
    path('mcp-imports/<int:pk>/', views.McpConversationImportDetailView.as_view()),
    path('mcp-imports/', views.McpConversationImportListCreateView.as_view()),
    path('source-promotions/', views.SourcePromotionListView.as_view()),
    path('promotions/to-subject/', views.PromoteToSubjectView.as_view()),
]
