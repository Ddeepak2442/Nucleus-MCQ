from django.urls import path
from .views import HomeView,SubjectView, TopicListView

urlpatterns = [
    path('home/', HomeView.as_view(), name='home_new'),
    path('subjects/', SubjectView.as_view(), name='subject_list'),
    path('subjects/<str:subject_slug>/topics/', TopicListView.as_view(), name='topic_list'),
] 

