from django.urls import path

from . import views

app_name = 'reviews'

urlpatterns = [
    path('reviews/due/', views.ReviewDueListView.as_view()),
    path('reviews/<int:bite_id>/grade/', views.ReviewGradeView.as_view()),
    path('reviews/weekly-progress/<int:subject_id>/', views.SubjectGoalProgressView.as_view()),
    path('subject-goals/', views.SubjectWeeklyGoalListCreateView.as_view()),
    path('subject-goals/<int:pk>/', views.SubjectWeeklyGoalDetailView.as_view()),
]
