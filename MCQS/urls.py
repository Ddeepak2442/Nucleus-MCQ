from django.urls import path
from .views import HomeView,  SubjectView, TopicListView,MCQQuizView, update_question_history

urlpatterns = [
    path('home/', HomeView.as_view(), name='home_new'),
    path('subjects/', SubjectView.as_view(), name='subject_list'),
    path('subjects/<str:subject_slug>/topics/', TopicListView.as_view(), name='topic_list'),
    path('topics/<str:topic_slug>/<int:question_num>/',MCQQuizView.as_view(), name='mcq_quiz'),
    path('update_question_history/', update_question_history, name='update_question_history'),
    
]
