from django import forms
from .models import Note

class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ['user_note']
        widgets = {
            'user_note': forms.Textarea(attrs={'placeholder': 'Add your note here...'}),
        }
