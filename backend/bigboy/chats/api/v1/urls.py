from django.urls import path

from rest_framework.schemas import get_schema_view

from . import views

schema_view = get_schema_view(title='Chats API')

app_name = 'chats'
urlpatterns = [
    path('chats/', views.WhatsAppWebhook.as_view()),
]