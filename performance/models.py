from django.db import models

from Accounts.models import Account
from django.conf import settings
# Create your models here.

class user_performance(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,  on_delete=models.SET_NULL,null=True)
    attempted_ques =models.TextField()
    answered_correct =models.TextField()
    bookmark_ques =models.TextField(blank=True,null=True)
    revise_ques =models.TextField(blank=True,null=True)

    def __str__(self):
        return self.user.email
