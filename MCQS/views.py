from django.shortcuts import redirect, render, get_object_or_404
from django.http import HttpResponse
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView,TemplateView
from . models import Subject,Topic,Question
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



class TopicListView(ListView):
    model = Topic
    template_name = 'mcq/topic.html'
    context_object_name = 'topics'

    @method_decorator(login_required)
    def dispatch(    self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_queryset(self):
        request = self.request
        print("Request:", request)
        queryset = super().get_queryset()
        print("Original queryset:", queryset) 
        subject_slug = self.kwargs.get('subject_slug')
        print("Subject slug:", subject_slug) 
        if subject_slug:
            subject = get_object_or_404(Subject, slug=subject_slug)
            return queryset.filter(subject_name=subject).annotate(subtopic_count=Count('subtopic'))
        else:
            return queryset
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        subject_slug = self.kwargs.get('subject_slug')
        if subject_slug:
            subject = get_object_or_404(Subject, slug=subject_slug)
            context['subject'] = subject
        return context
    
def mcq_quiz(request, topic_slug, question_num):
    print("Debugging - Entered mcq_quiz view")
    
    topic = get_object_or_404(Topic, slug=topic_slug)
    print("Debugging - Retrieved topic:", topic)

    questions = Question.objects.filter(sub_topic_name__topic_name=topic)
    print("Debugging - Retrieved questions:", questions)
    
    if not questions.exists() or question_num > len(questions) or question_num < 1:
        print("Debugging - Redirecting due to invalid question number or empty question queryset")
        return redirect('topic_list', subject_slug=topic.subject.slug)  # Redirect to topic list or some other page

    current_question = questions[question_num - 1]
    print("Debugging - Retrieved current question:", current_question)

    opt_values = current_question.opt_values.split(';') if current_question.opt_values else []
    print("Debugging - Retrieved options:", opt_values)

    context = {
        'topic': topic,
        'current_question': current_question,
        'opt_values': opt_values,
        'question_num': question_num,
        'total_questions': len(questions),
    }
    
    print("Debugging - Rendering mcq.html template with context:", context)
    return render(request, 'mcq/mcq.html', context)
