from django.shortcuts import get_object_or_404 ,render 
from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.http import JsonResponse
from Accounts.models import UserProfile
from .models import user_performance
from MCQS.models import Subject, Question,Topic,SubTopic
from django.core.paginator import EmptyPage, PageNotAnInteger,Paginator


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


# class TopicPerformanceView(LoginRequiredMixin, View):
#     template_name = 'performance/performance_topic.html'

#     def get(self, request, *args, **kwargs):
#         context = self.get_context_data(request)
#         return render(request, self.template_name, context)

#     def get_context_data(self, request):
#         current_user = request.user
#         subtopic = SubTopic.objects.all()  # Assuming SubTopic is the correct model here

#         topic_performance_data = self.calculate_performance_data(current_user, subtopics)

#         return {'subtopics': subtopics, 'topic_performance_data': topic_performance_data}


        
#     def get_topic_name_by_id(self, topic_id):
#         try:
#             topic = Topic.objects.get(id=topic_id)
#             return topic.topic_name
#         except Topic.DoesNotExist:
#             return "Unknown Topic"
    
#     def calculate_performance_data(self, user, topics):
#         user_perf = user_performance.objects.get(user=user)
#         answered_correct_ids = [id for id in user_perf.answered_correct.split(';') if id]
#         answered_correct_ids = [int(id) for id in answered_correct_ids if id.isdigit()]

#         total_questions_per_topic = self.get_total_questions_per_topic(topics)  # Ensure only one argument is passed
#         correct_answers_per_topic = self.get_correct_answers_per_topic( answered_correct_ids)

#         performance_data = {}
#         for topic in total_questions_per_topic:
#             topic_name = topic['sub_topic_name__topic_name']
#             total_questions = topic['total']
#             correct_answers = next((item['correct'] for item in correct_answers_per_topic if item['sub_topic_name__topic_name'] == topic_name), 0)
#             performance_percentage = self.calculate_performance_percentage(correct_answers, total_questions)
#             performance_data[topic_name] = {'percentage': performance_percentage}
#         return performance_data

class TopicPerformanceView(LoginRequiredMixin, View):
    template_name = 'performance/performance_topic.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(request)
        return render(request, self.template_name, context)

    def get_context_data(self, request):
        current_user=request.user
        topics = Topic.objects.all()
        
        performance_data = self.calculate_performance_data(current_user)
        return {'topics': topics, 'performance_data': performance_data}
    def get_topic_name_by_id(self, topic_id):
        try:
            topic = Topic.objects.get(id=topic_id)
            return topic.topic_name
        except Topic.DoesNotExist:
            return "Unknown Subject"
    

    def calculate_performance_data(self, user):
        user_perf = user_performance.objects.get(user=user)
        answered_correct_ids = [id for id in user_perf.answered_correct.split(';') if id]
        # Convert to integers to ensure they are valid IDs
        answered_correct_ids = [int(id) for id in answered_correct_ids if id.isdigit()]
        #print(answered_correct_ids)

        total_questions_per_topic = self.get_total_questions_per_topic()
        correct_answers_per_topic = self.get_correct_answers_per_topic(answered_correct_ids)
        print(total_questions_per_topic)
        print(correct_answers_per_topic)

        performance_data = {}
        for topic in total_questions_per_topic:
            topic_id = topic['sub_topic_name__topic_name']
            topic_name = self.get_topic_name_by_id(topic_id)
             
            total_questions = topic['total']
            correct_answers = next((item['correct'] for item in correct_answers_per_topic if item['sub_topic_name__topic_name'] == topic_id), 0)
            performance_percentage = self.calculate_performance_percentage(correct_answers, total_questions)
            performance_data[topic_name] =   {'topic_name': topic_name,'percentage': performance_percentage}
        return performance_data

    def get_total_questions_per_topic(self):
        

        return Question.objects.values('sub_topic_name__topic_name').annotate(total=Count('id'))


    def get_correct_answers_per_topic(self, answered_correct_ids):
        return Question.objects.filter(id__in=answered_correct_ids).values('sub_topic_name__topic_name').annotate(correct=Count('id'))

    def calculate_performance_percentage(self, correct_answers, total_questions):
        percentage = (correct_answers / total_questions) * 100 if total_questions else 0
        return round(percentage)
  


    # def get_total_questions_per_topic(self, topics):
    #     return Question.objects.values('sub_topic_name__topic_name').annotate(total=Count('id'))
    #     #return Question.objects.filter(sub_topic_name__topic_name__in=topics).values('sub_topic_name__topic__topic_name').annotate(total=Count('id'))



    # def get_correct_answers_per_topic(self, answered_correct_ids):
    #     return Question.objects.filter(id__in=answered_correct_ids).values('sub_topic_name__topic_name').annotate(correct=Count('id'))

    # def calculate_performance_percentage(self, correct_answers, total_questions):
    #     percentage = (correct_answers / total_questions) * 100 if total_questions else 0
    #     return round(percentage)
