from django.urls import path
from . import views

urlpatterns = [
    path('performance/', views.PerformanceView.as_view(), name='performance'),
    path('performance/attempted-questions/', views.get_attempted_questions, name='get_attempted_questions'),
    path('topic-performance/<slug:subject_slug>/', views.TopicPerformanceView.as_view(), name='topic_performance'),
    path('important-questions/', views.get_important_questions, name='important_questions'),
    #path('star-questions/', views.get_star_questions, name='star_questions'),
    path('doubt-questions/', views.get_doubt_questions, name='doubt_questions'),
    path('performance/<slug:subject_slug>/summary/', views.PerformanceSummaryView.as_view(), name='performance_summary'),
     
]


