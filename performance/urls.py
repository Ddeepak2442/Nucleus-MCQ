from django.urls import path
from . import views

urlpatterns = [
    path('performance/', views.PerformanceView.as_view(), name='performance'),
    path('performance/attempted-questions/', views.get_attempted_questions, name='get_attempted_questions'),
    path('topic-performance/<slug:subject_slug>/', views.TopicPerformanceView.as_view(), name='topic_performance'),
    path('important-questions/', views.get_important_questions, name='important_questions'),
     
]


