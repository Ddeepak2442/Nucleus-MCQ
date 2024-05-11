from django.db import models
from MCQS.models import SubTopic
from django.utils.text import slugify

class Note(models.Model):
    sub_topic_name = models.ForeignKey(SubTopic, on_delete=models.CASCADE)
    note = models.TextField()
    slug = models.SlugField(unique=True, max_length=255, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.note)[:50]  # Generating slug from the note field
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.sub_topic_name} - {self.note}"
    
    #  def __str__(self):
    #     return f"{self.note}"

