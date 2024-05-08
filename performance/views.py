from django.forms import SlugField
from django.shortcuts import get_object_or_404 ,render 
from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from .models import user_performance
from MCQS.models import Subject, Question,Topic,SubTopic
from django.core.paginator import Paginator
from django.views.generic import TemplateView
from django.http import HttpResponseBadRequest
import openai,os
from dotenv import load_dotenv
from openai import OpenAI
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY",None)
openai.api_key=api_key
client = OpenAI(api_key=api_key)

class PerformanceView(LoginRequiredMixin, View):
    template_name = 'performance/performance.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(request)
        return render(request, self.template_name, context)

    def get_context_data(self, request):
        current_user=request.user
        subjects = Subject.objects.all()
        
        performance_data = self.calculate_performance_data(current_user)
        return {'subjects': subjects, 'performance_data': performance_data}
    def get_subject_name_by_id(self, subject_id):
        try:
            subject = Subject.objects.get(id=subject_id)
            return subject.subject_name
        except Subject.DoesNotExist:
            return "Unknown Subject"
    

    def calculate_performance_data(self, user):
        user_perf = user_performance.objects.get(user=user)
        answered_correct_ids = [id for id in user_perf.answered_correct.split(';') if id]
        # Convert to integers to ensure they are valid IDs
        answered_correct_ids = [int(id) for id in answered_correct_ids if id.isdigit()]
        #print(answered_correct_ids)

        total_questions_per_subject = self.get_total_questions_per_subject()
        correct_answers_per_subject = self.get_correct_answers_per_subject(answered_correct_ids)
        print(total_questions_per_subject)
        print(correct_answers_per_subject)

        performance_data = {}
        for subject in total_questions_per_subject:
            subject_id = subject['sub_topic_name__topic_name__subject_name']
            subject_name = self.get_subject_name_by_id(subject_id)
            subject_image = Subject.objects.get(id=subject_id).subject_image  # Fetch subject image
            total_questions = subject['total']
            correct_answers = next((item['correct'] for item in correct_answers_per_subject if item['sub_topic_name__topic_name__subject_name'] == subject_id), 0)
            performance_percentage = self.calculate_performance_percentage(correct_answers, total_questions)
            performance_data[subject_name] =   {'percentage': performance_percentage, 'image': subject_image}
        return performance_data

    def get_total_questions_per_subject(self):
        return Question.objects.values('sub_topic_name__topic_name__subject_name').annotate(total=Count('id'))


    def get_correct_answers_per_subject(self, answered_correct_ids):
        return Question.objects.filter(id__in=answered_correct_ids).values('sub_topic_name__topic_name__subject_name').annotate(correct=Count('id'))

    def calculate_performance_percentage(self, correct_answers, total_questions):
        percentage = (correct_answers / total_questions) * 100 if total_questions else 0
        return round(percentage)
  


def get_attempted_questions(request):
    user_perf_instance = get_object_or_404(user_performance, user=request.user)
    attempted_questions_string = user_perf_instance.attempted_ques
    attempted_questions_list = [question_id for question_id in attempted_questions_string.split(';') if question_id.strip()]
    unique_attempted_questions = set(attempted_questions_list)

    # Fetch all attempted questions
    attempted_questions = Question.objects.filter(id__in=unique_attempted_questions)

    # Create a list to store attempted questions data
    attempted_questions_data = []

    # Loop through attempted questions to prepare data
    for question in attempted_questions:
        # Split opt_values by semicolon to get options
        options = question.opt_values.split(';')
        
        attempted_question = {
            'id': question.id,
            'question': question.question,
            'options': options,
            'explanation': question.explanation,
        }
        attempted_questions_data.append(attempted_question)

    paginator = Paginator(attempted_questions_data, 10)  # Show 10 questions per page

    page_number = request.GET.get('page')
    attempted_questions_page = paginator.get_page(page_number)

    return render(request, 'home.html', {'attempted_questions': attempted_questions_page})

    
class TopicPerformanceView(LoginRequiredMixin, View):
    template_name = 'performance/performance_topic.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(request, *args, **kwargs)  # Pass args and kwargs
        return render(request, self.template_name, context)


    def get_context_data(self, request,**kwargs):
        current_user = request.user
        subjects = Subject.objects.all()
        subject_slug =  kwargs.get('subject_slug') 
        topic_id = kwargs.get('topic_id')
        print("subject_slug:",subject_slug)
        selected_subject = None
        selected_topic = None 
        if  subject_slug:
            selected_subject = get_object_or_404(Subject, slug=subject_slug)

        topics = None
        performance_data = None

        if selected_subject:
            topics =  Topic.objects.filter(subject_name=selected_subject)
            if topic_id:
              selected_topic = get_object_or_404(Topic, id=topic_id)

            performance_data = self.calculate_performance_data(current_user, selected_subject)
        
        # Add 'subject_name' to the context
        subject_name = selected_subject.subject_name if selected_subject else None
        return {
            'subjects': subjects,
            'selected_subject': selected_subject,
            'subject_name': subject_name, 
            'topics': topics,
            'selected_topic': selected_topic,  
            'performance_data': performance_data
    }


    def calculate_performance_data(self, user, subject=None):
        try:
            # Retrieve user performance data
            user_perf = user_performance.objects.get(user=user)
            print(user_perf)

            # Extract and validate answered correct IDs
            answered_correct_ids = [int(id) for id in user_perf.answered_correct.split(';') if id.isdigit()]
            valid_answered_correct_ids = Question.objects.filter(id__in=answered_correct_ids).values_list('id', flat=True)
            print(answered_correct_ids)
            # Filter out invalid IDs
            answered_correct_ids = list(valid_answered_correct_ids)
            print(valid_answered_correct_ids)
        except user_performance.DoesNotExist:
            print("User performance data does not exist for user:", user)
            answered_correct_ids = []

     # Retrieve total questions per topic and correct answers per topic
        total_questions_per_topic = self.get_total_questions_per_topic(subject)
        correct_answers_per_topic = self.get_correct_answers_per_topic(answered_correct_ids, subject)
        print(total_questions_per_topic)
        print(correct_answers_per_topic)
        
        print("Correct answers per topic:", correct_answers_per_topic)


        performance_data = {}

        for topic in total_questions_per_topic:
            topic_reference = topic['sub_topic_name__topic_name']
            # Assuming that topic_reference is an ID, use it to get the actual topic name
            actual_topic_name = Topic.objects.get(id=topic_reference).topic_name  # Replace 'name' with the actual field that stores the topic name
            total_questions = topic['total']
            correct_answers = next((item['correct'] for item in correct_answers_per_topic if item['sub_topic_name__topic_name'] == topic_reference), 0)
            performance_percentage = self.calculate_performance_percentage(correct_answers, total_questions)
            performance_data[actual_topic_name] = {'topic_name': actual_topic_name, 'percentage': performance_percentage}
        
            # Debug print statements
            print("Topic reference:", topic_reference)
            print("Actual topic name:", actual_topic_name)
            print("Total questions:", total_questions)
            print("Correct answers:", correct_answers)
            print("Performance percentage:", performance_percentage)

        return performance_data



    def get_total_questions_per_topic(self, subject=None):
        questions = Question.objects
        if subject:
            questions = questions.filter(sub_topic_name__topic_name__subject_name=subject)
            print("no.of questions in subject topics")
        total_questions_per_topic = questions.values('sub_topic_name__topic_name').annotate(total=Count('id'))
        print(total_questions_per_topic)
        print(total_questions_per_topic[0].keys() if total_questions_per_topic else "No data")
        print("Keys for total questions per topic:", total_questions_per_topic[0].keys() if total_questions_per_topic else "No data")
        return total_questions_per_topic
        

    def get_correct_answers_per_topic(self, answered_correct_ids, subject=None):
        #  queryset for questions
        print("Answered correct IDs:", answered_correct_ids)

        questions = Question.objects.filter(id__in=answered_correct_ids)

        # filter the questions by subject
        if subject:
            print("Filtering by subject:", subject)

            questions = questions.filter(sub_topic_name__topic_name__subject_name=subject)
            print("questions:",questions)
            #  `questions` queryset to calculate correct answers per topic
            correct_answers_per_topic = questions.values('sub_topic_name__topic_name').annotate(correct=Count('id'))
            print(correct_answers_per_topic)
            print("Correct answers per topic:", correct_answers_per_topic)
            print("Keys for correct answers per topic:", correct_answers_per_topic[0].keys() if correct_answers_per_topic else "No data")
            return correct_answers_per_topic

    


    def calculate_performance_percentage(self, correct_answers, total_questions):
        print("Calculating performance data...")

        percentage = (correct_answers / total_questions) * 100 if total_questions else 0
        return round(percentage)

    def get_topic_name_by_name(self, subject, topic_name):
        try:
        # Assuming `topic_id` is meant to reference a Topic object directly
           topic = Topic.objects.get(topic_name=topic_name)
           print(topic)
           return topic.topic_name
        except Topic.DoesNotExist:
            return "Unknown Topic"



def correct_answer(question_id):
    # Fetch the question object
    question = get_object_or_404(Question, id=question_id)
    
    # Split the options and correct options
    opt_values = question.opt_values.split(';')
    correct_options = question.correct_options.split(';')
    
    # Create a dictionary mapping correct options to their corresponding values
    correct_answers_dict = dict(zip(correct_options, opt_values))
    
    # Fetch the correct answer
    correct_answer = correct_answers_dict.get('1', None)  # Assuming '1' is the correct option
    
    return correct_answer

def get_important_questions(request):
    user_perf_instance = get_object_or_404(user_performance, user=request.user)
    important_questions_string = user_perf_instance.bookmark_ques
    important_questions_list = [question_id for question_id in important_questions_string.split(';') if question_id.strip()]
    unique_important_questions = set(important_questions_list)

    # Fetch all important questions
    important_questions = Question.objects.filter(id__in=unique_important_questions)

    # Create a list to store important questions data
    important_questions_data = []

    # Initialize subject_name and topic_name variables
    subject_name = None
    topic_name = None

    # Loop through important questions to prepare data
    for question in important_questions:
        # Split opt_values by semicolon to get options
        options = question.opt_values.split(';')
        
        # Get sub_topic_name and topic_name
        sub_topic_name = None
        if question.sub_topic_name:
            sub_topic_name = question.sub_topic_name.sub_topic_name
            if question.sub_topic_name.topic_name:
                topic_name = question.sub_topic_name.topic_name.topic_name
                if question.sub_topic_name.topic_name.subject_name:
                    subject_name = question.sub_topic_name.topic_name.subject_name.subject_name

        important_question = {
            'id': question.id,
            'question': question.question,
            'options': options,
            'explanation': question.explanation,
            'subject_name': subject_name,
            'topic_name': topic_name,
            'sub_topic_name': sub_topic_name,
        }
        important_questions_data.append(important_question)

    paginator = Paginator(important_questions_data, 10)  # Show 10 questions per page

    page_number = request.GET.get('page')
    important_questions_page = paginator.get_page(page_number)

    # Handle form submission
    feedback_color = None
    correct_ans = None
    selected_option = None
    if request.method == 'POST':
        selected_option = request.POST.get('selected_option')
        question_id = request.POST.get('question_id')
        correct_ans = correct_answer(question_id)
        feedback_color = 'green' if selected_option == correct_ans else 'red'

    return render(request, 'performance/important_question.html', {
        'important_questions': important_questions_page,
        'subject_name': subject_name,
        'topic_name': topic_name,
        'feedback_color': feedback_color,
        'correct_ans': correct_ans,
        'selected_option': selected_option,
    })


def get_doubt_questions(request):
    user_perf_instance = get_object_or_404(user_performance, user=request.user)
    doubt_questions_string = user_perf_instance.revise_ques
    doubt_questions_list = [question_id for question_id in doubt_questions_string.split(';') if question_id.strip()]
    unique_doubt_questions = set(doubt_questions_list)

    # Fetch all doubt questions
    doubt_questions = Question.objects.filter(id__in=unique_doubt_questions)

    # Create a list to store star questions data
    doubt_questions_data = []

    # Initialize subject_name and topic_name variables
    subject_name = None
    topic_name = None

    # Loop through doubt questions to prepare data
    for question in doubt_questions:
        # Split opt_values by semicolon to get options
        options = question.opt_values.split(';')
        
        # Get sub_topic_name and topic_name
        sub_topic_name = None
        if question.sub_topic_name:
            sub_topic_name = question.sub_topic_name.sub_topic_name
            if question.sub_topic_name.topic_name:
                topic_name = question.sub_topic_name.topic_name.topic_name
                if question.sub_topic_name.topic_name.subject_name:
                    subject_name = question.sub_topic_name.topic_name.subject_name.subject_name

        doubt_question = {
            'id': question.id,
            'question': question.question,
            'options': options,
            'explanation': question.explanation,
            'subject_name': subject_name,
            'topic_name': topic_name,
            'sub_topic_name': sub_topic_name,
        }
        doubt_questions_data.append(doubt_question)

    paginator = Paginator(doubt_questions_data, 10)  # Show 10 questions per page

    page_number = request.GET.get('page')
    doubt_questions_page = paginator.get_page(page_number)

    # Handle form submission
    feedback_color = None
    correct_ans = None
    selected_option = None
    if request.method == 'POST':
        selected_option = request.POST.get('selected_option')
        question_id = request.POST.get('question_id')
        correct_ans = correct_answer(question_id)
        feedback_color = 'green' if selected_option == correct_ans else 'red'

    return render(request, 'performance/doubt_question.html', {
        'doubt_questions': doubt_questions_page,
        'subject_name': subject_name,
        'topic_name': topic_name,
        'feedback_color': feedback_color,
        'correct_ans': correct_ans,
        'selected_option': selected_option,
        'explanation': question.explanation,

    })



class PerformanceSummaryView(LoginRequiredMixin,TemplateView):
    template_name = 'performance/performance_summary.html'

    def call_gpt(self, user_input):
        """
        Method to call the GPT model and return the result.
        """
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an helpfull assistant for a medical student to prepare medical exams."},
                    {"role": "user", "content": user_input}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"An error occurred: {e}")
            return "An error occurred while generating the summary."
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(request, *args, **kwargs)  # Pass args and kwargs
        return render(request, self.template_name, context)
    def get_context_data(self, request,**kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        request = self.request  # Access the request object
        current_user = request.user
        subjects = Subject.objects.all()
        subject_slug = kwargs.get('subject_slug')
        topic_id = kwargs.get('topic_id')

        selected_subject = None
        selected_topic = None
        performance_data = None

        # Check if a subject slug is provided and get the corresponding subject
        if subject_slug:
            selected_subject = get_object_or_404(Subject, slug=subject_slug)
            # If a topic ID is provided, get the corresponding topic
            if topic_id:
                selected_topic = get_object_or_404(Topic, id=topic_id)
            # Calculate performance data for the selected subject
            performance_data = self.calculate_performance_data(current_user, selected_subject)

        #  Prepare additional context
        context.update({
            'subjects': subjects,
            'selected_subject': selected_subject,
            'subject_name': selected_subject.subject_name if selected_subject else None,
            'topics': Topic.objects.filter(subject_name=selected_subject) if selected_subject else None,
            'selected_topic': selected_topic,
            'performance_data': performance_data
        })
        return context

    
    def calculate_performance_data(self, user, subject=None):
        try:
            # Retrieve user performance data
            user_perf = user_performance.objects.get(user=user)
            print(user_perf)

            # Extract and validate answered correct IDs
            answered_correct_ids = [int(id) for id in user_perf.answered_correct.split(';') if id.isdigit()]
            valid_answered_correct_ids = Question.objects.filter(id__in=answered_correct_ids).values_list('id', flat=True)
            print(answered_correct_ids)
            # Filter out invalid IDs
            answered_correct_ids = list(valid_answered_correct_ids)
            print(valid_answered_correct_ids)
        except user_performance.DoesNotExist:
            print("User performance data does not exist for user:", user)
            answered_correct_ids = []

     # Retrieve total questions per topic and correct answers per topic
        total_questions_per_topic = self.get_total_questions_per_topic(subject)
        correct_answers_per_topic = self.get_correct_answers_per_topic(answered_correct_ids, subject)
        print(total_questions_per_topic)
        print(correct_answers_per_topic)
        
        print("Correct answers per topic:", correct_answers_per_topic)


        performance_data = {}

        for topic in total_questions_per_topic:
            topic_reference = topic['sub_topic_name__topic_name']
            # Assuming that topic_reference is an ID, use it to get the actual topic name
            actual_topic_name = Topic.objects.get(id=topic_reference).topic_name  # Replace 'name' with the actual field that stores the topic name
            total_questions = topic['total']
            correct_answers = next((item['correct'] for item in correct_answers_per_topic if item['sub_topic_name__topic_name'] == topic_reference), 0)
            performance_percentage = self.calculate_performance_percentage(correct_answers, total_questions)
            performance_data[actual_topic_name] = {'topic_name': actual_topic_name, 'percentage': performance_percentage}
        
            # Debug print statements
            print("Topic reference:", topic_reference)
            print("Actual topic name:", actual_topic_name)
            print("Total questions:", total_questions)
            print("Correct answers:", correct_answers)
            print("Performance percentage:", performance_percentage)

        return performance_data



    def get_total_questions_per_topic(self, subject=None):
        questions = Question.objects
        if subject:
            questions = questions.filter(sub_topic_name__topic_name__subject_name=subject)
            print("no.of questions in subject topics")
        total_questions_per_topic = questions.values('sub_topic_name__topic_name').annotate(total=Count('id'))
        print(total_questions_per_topic)
        print(total_questions_per_topic[0].keys() if total_questions_per_topic else "No data")
        print("Keys for total questions per topic:", total_questions_per_topic[0].keys() if total_questions_per_topic else "No data")
        return total_questions_per_topic
        

    def get_correct_answers_per_topic(self, answered_correct_ids, subject=None):
        #  queryset for questions
        print("Answered correct IDs:", answered_correct_ids)

        questions = Question.objects.filter(id__in=answered_correct_ids)

        # filter the questions by subject
        if subject:
            print("Filtering by subject:", subject)

            questions = questions.filter(sub_topic_name__topic_name__subject_name=subject)
            print("questions:",questions)
            #  `questions` queryset to calculate correct answers per topic
            correct_answers_per_topic = questions.values('sub_topic_name__topic_name').annotate(correct=Count('id'))
            print(correct_answers_per_topic)
            print("Correct answers per topic:", correct_answers_per_topic)
            print("Keys for correct answers per topic:", correct_answers_per_topic[0].keys() if correct_answers_per_topic else "No data")
            return correct_answers_per_topic

    


    def calculate_performance_percentage(self, correct_answers, total_questions):
        print("Calculating performance data...")

        percentage = (correct_answers / total_questions) * 100 if total_questions else 0
        return round(percentage)

    def get_topic_name_by_name(self, subject, topic_name):
        try:
        # Assuming `topic_id` is meant to reference a Topic object directly
           topic = Topic.objects.get(topic_name=topic_name)
           print(topic)
           return topic.topic_name
        except Topic.DoesNotExist:
            return "Unknown Topic"


    def post(self, request, *args, **kwargs):
        user_input = request.POST.get('user_input')
        prompt= ""
        if not user_input:
            return HttpResponseBadRequest("User input is required.")

        result = self.call_gpt(user_input)
        context = self.get_context_data(request,result=result)
        return render(request, self.template_name, context)
