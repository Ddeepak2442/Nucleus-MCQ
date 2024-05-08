from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.shortcuts import render
from django.http import HttpResponseBadRequest
import openai,os
from dotenv import load_dotenv
from openai import OpenAI
from django.db.models import Count
from performance.models import user_performance
from MCQS.models import Subject, Question,Topic,SubTopic
from .forms import HealthForm 


load_dotenv()

api_key = os.getenv("OPENAI_API_KEY",None)
openai.api_key=api_key
client = OpenAI(api_key=api_key)

def index(request):
    return render(request, 'index.html')

class GenerateSummaryView(LoginRequiredMixin,TemplateView):
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

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)  # Correctly use super() with TemplateView
        current_user = self.request.user
        
        context['subjects'] = Subject.objects.all()
        performance_data = self.calculate_performance_data(current_user)
        context['performance_data'] = performance_data
        if 'result' in kwargs:
            context['result'] = kwargs['result']
        return context

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
        context = self.get_context_data(result=result)
        return render(request, self.template_name, context)


class DietPlanView(LoginRequiredMixin,TemplateView):
    template_name = 'diet-plan.html'

    def call_gpt(self, prompt):
        """
        Method to call the GPT model and return the result.
        """
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional dietician."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"An error occurred: {e}")
            return "An error occurred while generating the summary."
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(request)
        return render(request, self.template_name, context)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)  # Correctly use super() with TemplateView
        form=HealthForm()
        context.setdefault('form', HealthForm())
        current_user = self.request.user
        return context
    def post(self, request, *args, **kwargs):
        form = HealthForm(request.POST) 
        if form.is_valid():
            name = form.cleaned_data.get('name')
            age = form.cleaned_data.get('age')
            weight = form.cleaned_data.get('weight')
            height = form.cleaned_data.get('height')
            gender = form.cleaned_data.get('gender')
            dietary_preferences = form.cleaned_data.get('diet')
            activity_level = form.cleaned_data.get('activity_level')
            dietary_restrictions = form.cleaned_data.get('dietary_restrictions')
            goal = form.cleaned_data.get('goal')
            prompt = f"prepare a comprehensive 90-day diet plan. Here are my details: Name: {name}, Age: {age}, Gender: {gender}, Weight: {weight} kg, Height: {height} cm, Dietary Preferences: {dietary_preferences}, Activity Level: {activity_level}, Dietary Restrictions: {dietary_restrictions}, Goal: {goal}. generate a report with date,name,age,gender,height,weight,bmi,fat%,body age,bmr,visceral fat %,substaneous fat %,trunk fat %,muscle%.Please format the plan in a table with daily meal suggestions."
            result = self.call_gpt(prompt)
            print(result)
            context = self.get_context_data(form=form, result=result) 
        else:
            context = self.get_context_data(form=form)

        return render(request, self.template_name, context)
