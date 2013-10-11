from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class ServiceUser(models.Model):

	auth = models.ForeignKey(User)

	def __str__(self):
		return self.auth.__str__()
