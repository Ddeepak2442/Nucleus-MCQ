from django.db import models
from MCQS.models import SubTopic
from django.utils.text import slugify

class Note(models.Model):
    sub_topic_name = models.ForeignKey(SubTopic, on_delete=models.CASCADE)
    note = models.TextField()
    user_note = models.TextField(blank= True,null=True)

    

    def __str__(self):
        return f"{self.sub_topic_name} "
    
    

