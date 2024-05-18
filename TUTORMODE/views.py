from django.http import   JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.shortcuts import get_object_or_404
from django.views.generic import ListView,TemplateView
from django.db.models import Count
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from MCQS.models import SubTopic, Subject, Topic
from .models import Note 
from TUTORMODE.form import NoteForm
import json 
import openai,os
from dotenv import load_dotenv
from openai import OpenAI
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY",None)
openai.api_key=api_key
client = OpenAI(api_key=api_key)


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
        print("Inside get_context_data method")  
    
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
    template_name = 'tutormode/note.html'
    def get_sub_topic_by_name(self, sub_topic_name):
        return get_object_or_404(SubTopic, sub_topic_name=sub_topic_name)

    def get_context_data(self, **kwargs):
        print("Inside get_context_data method of note")  # Add this line for debugging
        context = super().get_context_data(**kwargs)
        subject_slug = kwargs.get('subject_slug')
        topic_slug = kwargs.get('topic_slug')
        sub_topic_slug = kwargs.get('sub_topic_slug')
        sub_topic_instance = None
        notes = []
        user_note =[]
        result = []

        try:
            print("Querying SubTopic with slug:", sub_topic_slug)  # Debug statement
            sub_topic_instance = SubTopic.objects.get(slug=sub_topic_slug)
            print("SubTopic instance retrieved:", sub_topic_instance)  # Debug statement
            notes = Note.objects.filter(sub_topic_name=sub_topic_instance)
            context['subject_slug'] = subject_slug
            context['topic_slug'] = topic_slug
            context['sub_topic'] = sub_topic_instance
            context['form'] = NoteForm()
            context['user_notes'] = [note.user_note for note in notes if note.user_note]
    
            if sub_topic_instance is not None:
                context['sub_topic_name'] = sub_topic_instance.sub_topic_name
                context['sub_topic_slug'] = sub_topic_instance.slug
                print("Subtopic Name:", sub_topic_instance.sub_topic_name)
                #result = self.call_gpt(notes, user_note)
                #print("Generated MCQs:", result)  #for debug 
            else:
                context['error_message'] = "SubTopic not found."
            
        except  SubTopic.DoesNotExist:
            context['error_message'] = "SubTopic not found."
            print("SubTopic does not exist.") 
        except Exception as e:
            context['error_message'] = f"Error: {str(e)}"
            print(f"An error occurred: {str(e)}")  # Debug statement

        result = {
            "Question 1": {
                "Question": "What is medicine considered as from prehistoric times to recent centuries?",
                "Options": {
                    "a": "Purely a scientific field",
                    "b": "A combination of art and science",
                    "c": "Mainly a religious practice",
                    "d": "An art form only"
                },
                "correct_option": "b",
                "Explanation": "The notes mention that medicine has evolved from being an art closely tied to religious and philosophical beliefs to a combination of art and science in recent centuries."
            },
            "Question 2": {
                "Question": "Which term is used for alternative treatments outside of scientific medicine with ethical and efficacy concerns?",
                "Options": {
                    "a": "Folk medicine",
                    "b": "Prescientific medicine",
                    "c": "Traditional medicine",
                    "d": "Alternative medicine"
                },
                "correct_option": "d",
                "Explanation": "The notes explain that alternative treatments outside of scientific medicine, with ethical, safety, and efficacy concerns, are termed as alternative medicine."
            }
        }

        context['notes'] = notes
        context['result'] = result

        return context


    

    def add_user_note_to_subtopic(self, sub_topic_slug, user_note):
        try:
            sub_topic_instance = SubTopic.objects.get(slug=sub_topic_slug)
            note, created = Note.objects.get_or_create(sub_topic_name=sub_topic_instance, defaults={'user_note': user_note})

            if not created:
                note.user_note += f"\n{user_note}"
                note.save()
        except SubTopic.DoesNotExist:
            print("SubTopic with the provided slug does not exist.")
        except Exception as e:
            print(f"An error occurred: {str(e)}")

    def clear_user_note_for_subtopic(self, sub_topic_slug):
        try:
            sub_topic_instance = SubTopic.objects.get(slug=sub_topic_slug)
            note = Note.objects.get(sub_topic_name=sub_topic_instance)
            note.user_note = ""
            note.save()
            return JsonResponse({'message': 'User note cleared successfully'})
        except Note.DoesNotExist:
            print("Note not found")
            return JsonResponse({'error': 'Note not found'}, status=404)
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)
    
    def call_gpt(self, notes, user_note):
        """
        Method to call the GPT model and return the result.
        """
        prompt =''' 
                       note=\n{notes}     1. Summarize the notes
        ```
        Prompt: Please summarize the following notes and summary in a concise manner:\n\nNotes:\n{notes}\n\nSummary:\n{user_note}
        Notes:
        ${notes}
        ${user_note}

        ```

        2. Generate questions based on the summary
        ```
        Prompt: Based on the following summarized content, please generate 3 multiple-choice questions with 4 options each:

        ${summarized_content}
        ```

        3. Generate tough choices for two options
        ```
        Prompt 1: For the following question, please provide one challenging choice that is close to the correct answer but not quite right:

        Question: ${question_1}

        Prompt 2: For the following question, please provide another challenging choice that is close to the correct answer but not quite right:

        Question: ${question_2}
        ```

        4. Generate medium and easy choices for the other two options
        ```
        Prompt 1: For the following question, please provide one choice of medium difficulty that is related to the subject of the notes but not necessarily a correct answer to the specific question. You may look at other relevant sources to generate this choice:

        Question: ${question_1}
        Subject of notes: ${subject}

        Prompt 2: For the following question, please provide one easy choice that is related to the subject of the notes but not necessarily a correct answer to the specific question. You may look at other relevant sources to generate this choice:

        Question: ${question_2}
        Subject of notes: ${subject}
        The process we want to follow is:

        1. Summarize the `notes` variable into a single, concise summary using a prompt.
        2. Use the summarized content to generate multiple-choice questions with 4 options each, using another prompt.
        3. For each question generated in step 2, you want to create the following options:
           - Two challenging options that are close to the correct answer but not quite right. These options should be generated using a separate prompt that takes the question as input.
           - One medium difficulty option related to the subject of the notes but not necessarily the correct answer to the specific question.
           - One easy option related to the subject of the notes but not necessarily the correct answer to the specific question.
        4. For the medium and easy options in step 3, the prompt should be allowed to look at other relevant sources related to the subject of the notes to generate these options.

finally generate a 3 multiple choice questions from {notes}and {user_note}  based on the above mentioned conditions one by one clearly.  
Return your answer entirely in the form of a JSON code.Each MCQ should have question, include the options, the correct option, 
and a brief explanation of why the option is correct.Don't include anything other than the JSON.
'''
        print("prompt:",prompt)
        try:
            responses = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
                     {"role": "user", "content": prompt}
                    # {"role": "user", "content": prompt_tough_choices_1},
                    # {"role": "user", "content": prompt_tough_choices_2},
                    # {"role": "user", "content": prompt_medium_easy_1}
                ]
            )
            if isinstance(responses, list):
                result = []
                for response in responses:
                    result.append(response.choices[0].message.content)
                return result[:3]  # Return only the first three questions
            else:
                return [responses.choices[0].message.content]
           
        except Exception as e:
            print(f"An error occurred: {e}")
            return ["An error occurred while generating the MCQs."]

    def post(self, request, *args, **kwargs):

        action = request.POST.get('action')
        sub_topic_slug = kwargs.get('sub_topic_slug')
        print("sub_topic_slug:", sub_topic_slug)
        
        
        sub_topic_instance =  self.get_subtopic_by_slug(sub_topic_slug)
        print("sub_topic_instance:" ,sub_topic_instance)

        if action == 'add_note':
            user_note = request.POST.get('user_note')
            self.add_user_note_to_subtopic(sub_topic_slug, user_note)
        elif action == 'clear_note':
            self.clear_user_note_for_subtopic(sub_topic_slug)
        elif action == 'generate_mcq':
            # get notes based on the sub_topic_name 
            note = self.get_note_for_subtopic(sub_topic_instance)
            if note:
                user_note = note.user_note  # Get the user_note from the note instance
                print("note:", note.note)
                print("user_note:", user_note)
                result = self.call_gpt(note.note, user_note)
                print("result:", result)
                context = self.get_context_data(result=result)
        # Redirect back to the same page
        return redirect(request.path)
    def get_note_for_subtopic(self, sub_topic_instance):
        # Get the note for the given subtopic
        try:
            return Note.objects.get(sub_topic_name=sub_topic_instance)
        except Note.DoesNotExist:
            return None
    def get_subtopic_name_by_id(self, subtopic_id):
        try:
            subtopic = SubTopic.objects.get(id=subtopic_id)
            return subtopic.sub_topic_name
        except SubTopic.DoesNotExist:
            return "Unknown SubTopic"
    
    def get_subtopic_by_slug(self, sub_topic_slug):
        try:
            subtopic = SubTopic.objects.get(slug=sub_topic_slug)
            return subtopic
        except SubTopic.DoesNotExist:
            return None  # or handle this case as needed

        
