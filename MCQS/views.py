from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.views import View
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView,TemplateView,View
from django.contrib.auth.mixins import LoginRequiredMixin
from . models import Subject,Topic,Question,SubTopic
from performance.models import user_performance
from django.db.models import Count
from performance.forms import  ImportantQuestionForm,  DoubtQuestionForm
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


class HomeView(TemplateView):
    template_name = 'homenew.html'

class SubjectView(ListView):
    model = Subject
    template_name= 'mcq/subject.html'
    @method_decorator(login_required)
    def get(self, request):
       if request.method == 'GET':
            subjects = Subject.objects.annotate(num_topics=Count('topic')) # Retrieve all subjects from the database
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
        print("Inside get_context_data method")  # Add this line for debugging
    
        context = super().get_context_data(**kwargs)
        subject_slug = self.kwargs.get('subject_slug')
        if subject_slug:
          subject = get_object_or_404(Subject, slug=subject_slug)
          context['subject'] = subject
        return context
   
class MCQQuizView(LoginRequiredMixin, View):
    template_name = 'mcq/mcq.html'

    def get_context(self, request, topic_slug, question_num):
        feedback_color=None
        # Retrieve the Topic object
        topic = get_object_or_404(Topic, slug=topic_slug)
        print("Debugging - Retrieved topic:", topic)
        # Retrieve subtopics related to the topic
        sub_topics = SubTopic.objects.filter(topic_name=topic)
        print("Debugging - Retrieved subtopics:", sub_topics)
        # Number of QUESTIONS PRESENT IN SUBTOPIC
        for sub_topic in sub_topics:
          question_count = Question.objects.filter(sub_topic_name=sub_topic).count()
          sub_topic.question_count = question_count
          print(f"Subtopic '{sub_topic.sub_topic_name}' has {question_count} questions")

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
        correct_options_list = current_question.correct_options.split(';')

        # Construct URL for back to topics
        back_to_topics_url = reverse('topic_list', kwargs={'subject_slug': topic.subject_name.slug})

        # Prepare context
        context = {
            'topic': topic,
            'sub_topics': sub_topics,
            'current_question': current_question,
            'opt_values': opt_values,
            'correct_options_list': correct_options_list,
            'question_num': question_num,
            'total_questions': len(questions),
            'feedback_color': feedback_color,
            'back_to_topics_url': back_to_topics_url,
        }

        return context

    def get(self, request, topic_slug, question_num ):
        context = self.get_context(request, topic_slug, question_num)

        return render(request, self.template_name, context)
    def correct_answer(self,question_id):
        question = get_object_or_404(Question,id=question_id)
        opt_values = question.opt_values.split(';')
        correct_options = question.correct_options.split(';')
        dic = dict(zip(correct_options,opt_values))    
        correcr_ans = dic['1']
        return correcr_ans
    
    def post(self, request, topic_slug, question_num):
        selected_option = request.POST.get('selected_option')
        question_id = request.POST.get('question_id')
        correct_ans = self.correct_answer(question_id)
        feedback_color = 'green' if selected_option == correct_ans else 'red'

        current_user = request.user
        try:
            user_history = user_performance.objects.get(user=current_user)
        except user_performance.DoesNotExist:
            user_history = user_performance.objects.create(user=current_user, attempted_ques='', answered_correct='')
            user_history.attempted_ques += question_id + ';'
        if selected_option == correct_ans:
            user_history.answered_correct += question_id + ';'

        user_history.save()

       
        context = self.get_context(request, topic_slug, question_num)
        context['correct_ans'] = correct_ans
        context['feedback_color'] = feedback_color
        
        context['selected_option'] = selected_option
        context['question_id'] = question_id
        context['messages'] = messages.get_messages(request)
                # Handling bookmark question form submission
        if 'important_form' in request.POST:
            important_form = ImportantQuestionForm(request.POST)
            if important_form.is_valid():
                question_ids = important_form.cleaned_data['question_ids']
                user_history.bookmark_ques += question_ids + ";"
                user_history.save()
        
        
        if 'doubt_form' in request.POST:
            doubt_form = DoubtQuestionForm(request.POST)
            if doubt_form.is_valid():
                question_ids = doubt_form.cleaned_data['question_ids']
                user_history.revise_ques += question_ids + ";"
                user_history.save()

        context['important_form'] = ImportantQuestionForm()
        context['doubt_form'] = DoubtQuestionForm()

        return render(request, self.template_name, context)

@csrf_exempt
def update_question_history(request):
    print("Entered update_question_history view")
    if request.method == 'POST':
        question_id = request.POST.get('question_id')
        action = request.POST.get('action')
        print(f"Action: {action}, Question ID: {question_id}")

        current_user = request.user
        if not current_user.is_authenticated:
            return JsonResponse({'status': 'error', 'message': 'User not authenticated'})

        try:
            user_history = user_performance.objects.get(user=current_user)
            message = ''  # Initialize an empty message string

            # Split the existing IDs into lists, remove any empty strings
            important_ids = [id for id in user_history.bookmark_ques.split(';') if id]
            #star_ids = [id for id in user_history.star_ques.split(';') if id]
            doubt_ids = [id for id in user_history.revise_ques.split(';') if id]

            # Toggle the presence of the question_id in the respective list
            if action == 'important':
                if question_id in important_ids:
                    important_ids.remove(question_id)
                    message = 'Question removed from bookmark questions.'
                else:
                    important_ids.append(question_id)
                    message = 'Question added to bookmark questions.'
                user_history.bookmark_ques = ';'.join(important_ids) + (';' if important_ids else '')


            elif action == 'doubt':
                if question_id in doubt_ids:
                    doubt_ids.remove(question_id)
                    message = 'Question removed from doubted questions.'
                else:
                    doubt_ids.append(question_id)
                    message = 'Question added to doubted questions.'
                user_history.revise_ques = ';'.join(doubt_ids) + (';' if doubt_ids else '')

            user_history.save()

            return JsonResponse({'status': 'success', 'message': message})
        except user_performance.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'User history not found'})
        except Exception as e:
            print(f"Error: {e}")  # Print any exception that occurs
            return JsonResponse({'status': 'error', 'message': 'An error occurred'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request'})
    


