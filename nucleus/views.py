from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View
from django.shortcuts import render
from django.http import HttpResponseBadRequest
import openai,os
from dotenv import load_dotenv
from openai import OpenAI

from django.db.models import Count
from django.http import JsonResponse
from Accounts.models import UserProfile
from performance.models import user_performance
from MCQS.models import Subject, Question,Topic,SubTopic

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY",None)
openai.api_key=api_key
client = OpenAI(api_key=api_key)

def index(request):
    return render(request, 'index.html')

class GenerateSummaryView(LoginRequiredMixin,View):
    template_name = 'summary.html'

    def call_gpt(self, user_input):
        """
        Method to call the GPT model and return the result.
        """
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a poetic assistant, skilled in explaining complex programming concepts with creative flair."},
                    {"role": "user", "content": user_input}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"An error occurred: {e}")
            return "An error occurred while generating the summary."
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(request)
        return render(request, self.template_name, context)

    # def get_context_data(self):
    #     try:
    #         current_user=self.request.user
    #     except AttributeError:
    #     # Handle the case where self.request is not available
    #         current_user = None
    #     subjects = Subject.objects.all()
        
        # performance_data = self.calculate_performance_data(current_user)
        # return {'subjects': subjects, 'performance_data': performance_data}
    def get_context_data(self, **kwargs):
        current_user=self.request.user
        data = super().get_context_data(**kwargs)
        data['subjects'] =  Subject.objects.all()
        performance_data = self.calculate_performance_data(current_user)
        data['performance_data'] = performance_data
        return data
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
            # subject_image = Subject.objects.get(id=subject_id).subject_image  # Fetch subject image
            total_questions = subject['total']
            correct_answers = next((item['correct'] for item in correct_answers_per_subject if item['sub_topic_name__topic_name__subject_name'] == subject_id), 0)
            performance_percentage = self.calculate_performance_percentage(correct_answers, total_questions)
            performance_data[subject_name] =   {'percentage': performance_percentage}
            # performance_data[subject_name] =   {'percentage': performance_percentage, 'image': subject_image}
        return performance_data

    def get_total_questions_per_subject(self):
        return Question.objects.values('sub_topic_name__topic_name__subject_name').annotate(total=Count('id'))


    def get_correct_answers_per_subject(self, answered_correct_ids):
        return Question.objects.filter(id__in=answered_correct_ids).values('sub_topic_name__topic_name__subject_name').annotate(correct=Count('id'))

    def calculate_performance_percentage(self, correct_answers, total_questions):
        percentage = (correct_answers / total_questions) * 100 if total_questions else 0
        return round(percentage)
  

    def post(self, request, *args, **kwargs):
        user_input = request.POST.get('user_input')
        prompt= ""
        if not user_input:
            return HttpResponseBadRequest("User input is required.")

        result = self.call_gpt(user_input)
        context = self.get_context_data()
        context['result'] = result 
        return render(request, self.template_name, context)
