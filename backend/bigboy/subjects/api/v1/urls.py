from django.urls import path

from rest_framework.schemas import get_schema_view

from . import views

schema_view = get_schema_view(title='Subjects API')

app_name = 'subjects'
urlpatterns = [
    path('subjects/', views.SubjectListCreateView.as_view()),
    path('subjects/<int:subject_id>/progress/', views.SubjectProgressView.as_view()),
    path('subjects/<int:pk>/', views.SubjectRetrieveUpdateView.as_view()),
    path('topics/', views.TopicListCreateView.as_view()),
    path('topics/<int:pk>/regenerate-bites/', views.TopicRegenerateBitesView.as_view()),
    path('topics/<int:pk>/', views.TopicRetrieveUpdateView.as_view()),
    path('bites/<int:pk>/', views.BiteRetrieveUpdateView.as_view()),
    path('enrollments/', views.EnrollmentListCreateView.as_view()),
    path('enrollments/<int:pk>/', views.EnrollmentDestroyView.as_view()),
    path('bites/<int:bite_id>/complete/', views.BiteCompleteView.as_view()),
]