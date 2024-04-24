from django.urls import path
from . import views

urlpatterns = [
    path('performance/', views.PerformanceView.as_view(), name='performance'),
    path('performance/attempted-questions/', views.get_attempted_questions, name='get_attempted_questions'),
] 
