from django.contrib import admin
from .models import Note

@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('sub_topic_name', 'note', 'slug')
    list_filter = ('sub_topic_name',)  # Add filter options for SubTopic
    search_fields = ['note']

