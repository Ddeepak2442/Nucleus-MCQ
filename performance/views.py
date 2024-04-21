from django.shortcuts import render
from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count

from MCQS.models import Subject, Question
from .models import user_performance

class PerformanceView(LoginRequiredMixin, View):
    template_name = 'performance.html'

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
            total_questions = subject['total']
            correct_answers = next((item['correct'] for item in correct_answers_per_subject if item['sub_topic_name__topic_name__subject_name'] == subject_id), 0)
            performance_percentage = self.calculate_performance_percentage(correct_answers, total_questions)
            performance_data[subject_name] = performance_percentage
        return performance_data

    def get_total_questions_per_subject(self):
        return Question.objects.values('sub_topic_name__topic_name__subject_name').annotate(total=Count('id'))

    def get_correct_answers_per_subject(self, answered_correct_ids):
        return Question.objects.filter(id__in=answered_correct_ids).values('sub_topic_name__topic_name__subject_name').annotate(correct=Count('id'))

    def calculate_performance_percentage(self, correct_answers, total_questions):
        percentage = (correct_answers / total_questions) * 100 if total_questions else 0
        return round(percentage)