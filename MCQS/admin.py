from django.contrib import admin
from .models import Subject, Topic, SubTopic, Approver, Question

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('subject_name','subject_image')
    prepopulated_fields = {'slug': ('subject_name',)}
    list_filter = ('subject_name',)

@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('topic_name', 'subject_name')
    prepopulated_fields = {'slug': ('topic_name',)}
    list_filter = ('subject_name',)

@admin.register(SubTopic)
class SubTopicAdmin(admin.ModelAdmin):
    list_display = ('sub_topic_name', 'topic_name')
    prepopulated_fields = {'slug': ('sub_topic_name',)}
    list_filter = ( 'topic_name',)

@admin.register(Approver)
class ApproverAdmin(admin.ModelAdmin):
    list_display = ('approver_name', 'designation')

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('question','sub_topic_name','approver_name', 'created_at', 'visibility_flag')
    list_filter = ('sub_topic_name','approver_name', 'created_at', 'visibility_flag')