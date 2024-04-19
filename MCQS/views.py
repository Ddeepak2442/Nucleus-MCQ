from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView,TemplateView
from . models import Subject,Topic
from django.db.models import Count

from django.http import HttpRequest

class HomeView(TemplateView):
    template_name = 'home.html'
class SubjectView(ListView):
    model = Subject
    template_name= 'mcq/subject.html'
    @method_decorator(login_required)
    def get(self, request):
       if request.method == 'GET':
            subjects = Subject.objects.all()  # Retrieve all subjects from the database
            return render(request, self.template_name, {'subjects': subjects})

# class TopicView(ListView):
#     model = Topic
#     template_name= 'mcq/topic.html'
#     @method_decorator(login_required)
#     def get(self, request):
#        if request.method == 'GET':
#             subject_slug = Subject.subject_name
#             subjects= Subject.objects.all()  # Retrieve all subjects from the database
#             topic = Topic
#             return render(request, self.template_name, {'subjects': subjects})

class TopicListView(ListView):
    model = Topic
    template_name = 'mcq/topic.html'
    context_object_name = 'topics'

    @method_decorator(login_required)
    def get_queryset(self):
        subject_slug = self.Kwargs['subject_slug']
        subject = get_object_or_404(Subject, slug=subject_slug)
        return Topic.objects.filter(subject=subject).annotate(subtopic_count=Count('subtopic'))
        
