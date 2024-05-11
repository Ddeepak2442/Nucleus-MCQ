from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.views.generic import ListView,TemplateView
from django.db.models import Count
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from MCQS.models import SubTopic, Subject, Topic
from django.urls import reverse

# Create your views here.
#### ------------------------views for Tutor Mode---------------------------------

class SubjectTutorView(ListView):
    model = Subject
    template_name= 'tutormode/subjecttutor.html'
    @method_decorator(login_required)
    def get(self, request):
       if request.method == 'GET':
            subjects = Subject.objects.annotate(num_topics=Count('topic')) # Retrieve all subjects from the database
            return render(request, self.template_name, {'subjects': subjects})
class TopicTutorListView(ListView):
    model = Topic
    template_name = 'tutormode/topic_tutor.html'
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

class SubTopicTutorListView(ListView):
    model = SubTopic
    template_name = 'tutormode/subtopic_tutor.html'
    context_object_name = 'subtopics'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_queryset(self):
        subject_slug = self.kwargs.get('subject_slug')
        topic_slug = self.kwargs.get('topic_slug')

        if subject_slug and topic_slug:
            subject = get_object_or_404(Subject, slug=subject_slug)
            topic = get_object_or_404(Topic, slug=topic_slug)
            return SubTopic.objects.filter(topic_name=topic).annotate(sub_topic_name_count=Count('sub_topic_name'))
        else:
            return SubTopic.objects.none()  # Return an empty queryset if slugs are not provided

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        subject_slug = self.kwargs.get('subject_slug')
        topic_slug = self.kwargs.get('topic_slug')

        if subject_slug and topic_slug:
            subject = get_object_or_404(Subject, slug=subject_slug)
            topic = get_object_or_404(Topic, slug=topic_slug)

            # Retrieve subtopics related to the topic
            sub_topics = SubTopic.objects.filter(topic_name=topic)

            context.update({
                'subject': subject,
                'topic': topic,
                'sub_topics': sub_topics,
            })

        return context
class NoteView(TemplateView):
    template_name ='tutormode/note.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Access the  sub_topic_name from kwargs
        sub_topic_name = kwargs.get('sub_topic_name')
        # Add the sub_topic_name to the context
        context['sub_topic_name'] = sub_topic_name
        return context
    