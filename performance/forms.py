from django import forms
from .models import user_performance


class ImportantQuestionForm(forms.Form):
    question_ids = forms.CharField()

class StarQuestionForm(forms.Form):
    question_ids = forms.CharField()

class DoubtQuestionForm(forms.Form):
    question_ids = forms.CharField()
