from django.db import models
from django.contrib.auth.models import User

class Project(models.Model):
	manager 	= models.ForeignKey(User, related_name="Project Manager")
	name 		= models.CharField(max_length=50)
	description = models.CharField(max_length=140)
	status 		= models.CharField(max_length=50)
	phase 		= models.CharField(max_length=50)
	lines 		= models.IntegerField(default=0)
	loc_per_h 	= models.BooleanField(default=True)
	members		= models.ManyToManyField(User, related_name="Project Members")


	def __str__(self):
		return self.name +" (manager: " + self.manager.__str__() + ")"

class Worklog(models.Model):
	project 	= models.ForeignKey(Project)
	owner 		= models.ForeignKey(User)
	summary 	= models.CharField(max_length=140)
	description = models.CharField(max_length=300)
	hours 		= models.IntegerField(default=0)
	minutes 	= models.IntegerField(default=0)
	datestamp 	= models.DateTimeField(auto_now=False, auto_now_add=True)

	def __str__(self):
		return self.project.__str__() +" log (" +str(self.datestamp)+" )"


# Create your models here.
