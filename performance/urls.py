from django.urls import path
from . import views

urlpatterns = [
    path('performance/', views.PerformanceView.as_view(), name='performance'),
] 

