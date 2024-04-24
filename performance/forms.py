from django import forms
from .models import user_performance

class BookmarkForm(forms.ModelForm):
    class Meta:
        model = user_performance
        fields = []

    important_ques = forms.CharField(widget=forms.Textarea(attrs={'rows': 4, 'cols': 40}), required=False)
    doubt_ques = forms.CharField(widget=forms.Textarea(attrs={'rows': 4, 'cols': 40}), required=False)
    star_ques = forms.CharField(widget=forms.Textarea(attrs={'rows': 4, 'cols': 40}), required=False)
