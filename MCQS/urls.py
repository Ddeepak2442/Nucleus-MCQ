from django.urls import path
from .views import HomeView,SubjectView, TopicListView,mcq_quiz

urlpatterns = [
    path('home/', HomeView.as_view(), name='home_new'),
    path('subjects/', SubjectView.as_view(), name='subject_list'),
    path('subjects/<str:subject_slug>/topics/', TopicListView.as_view(), name='topic_list'),
    path('topics/<str:topic_slug>/<int:question_num>/', mcq_quiz, name='mcq_quiz'),
] 
