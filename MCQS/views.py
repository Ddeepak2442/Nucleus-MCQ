from django.shortcuts import redirect, render, get_object_or_404
from django.http import HttpResponse
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView,TemplateView,View
from django.contrib.auth.mixins import LoginRequiredMixin
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
    def dispatch(self, *args, **kwargs):
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

class MCQQuizView(LoginRequiredMixin, View):
    template_name = 'mcq/mcq.html'
    def get(self, request, topic_slug, question_num):
        # Retrieve the Topic object
        topic = get_object_or_404(Topic, slug=topic_slug)
        print("Debugging - Retrieved topic:", topic)

        # Retrieve questions for the topic
        questions = Question.objects.filter(sub_topic_name__topic_name=topic)
        print("Debugging - Retrieved questions:", questions)

        # Validate question number
        if not questions.exists() or question_num > len(questions) or question_num < 1:
            print("Debugging - Redirecting due to invalid question number or empty question queryset")
            return redirect('subject_list')

        # Select the current question
        current_question = questions[question_num - 1]
        print("Debugging - Retrieved current question:", current_question)

        # Extract options
        opt_values = current_question.opt_values.split(';') if current_question.opt_values else []
        print("Debugging - Retrieved options:", opt_values)

        # Prepare context
        context = {
            'topic': topic,
            'current_question': current_question,
            'opt_values': opt_values,
            'question_num': question_num,
            'total_questions': len(questions),
        }

        # Render template with context
        return render(request, self.template_name, context)
    
    def correct_answer(self,question_id):
        question = get_object_or_404(Question,id=question_id)
        opt_values = question.opt_values.split(';')
        correct_options = question.correct_options.split(';')
        dic = dict(zip(correct_options,opt_values))    
        correcr_ans = dic['1']
        return correcr_ans

    def post(self, request, topic_slug, question_num):
        if request.method == 'POST':
            selected_option = request.POST.get('selected_option')
            question_id = request.POST.get('question_id')
            correct_ans = self.correct_answer(question_id)
            if selected_option == correct_ans:
                print("correct answer")
            else:
                print("wrong answer")
            
            user=request.user,
        pass