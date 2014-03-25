from django.db import models
from django.contrib.auth.models import User

from django.utils import timezone

class TimelineEvent(models.Model):
	member 		= models.ForeignKey(User, related_name="event creator")
	datestamp 	= models.DateTimeField(auto_now=False, auto_now_add=True)
	title		= models.CharField(max_length=140)
	description	= models.CharField(max_length=255)
	category	= models.CharField(max_length=100)
	link		= models.CharField(max_length=255)
	related_key	= models.IntegerField()
	viewers		= models.ManyToManyField(User, related_name="allowed viewers")

	def __str__( self ):
		return str(self.datestamp) + " " + self.member.username + " " + self.title



class Project(models.Model):
	"""
	Defines a Project model which can have tags, 
	tasks, and additional members associated with it.

	This is the basis of the application.
	"""
	manager 	= models.ForeignKey(User, related_name="Project Manager")
	subprojects = models.ManyToManyField( 'Project', related_name="Subprojects" )
	parents		= models.ManyToManyField( 'Project', related_name="Parents" )
	name 		= models.CharField(max_length=50)
	description = models.CharField(max_length=140)
	status 		= models.CharField(max_length=50)
	phase 		= models.CharField(max_length=50)
	lines 		= models.IntegerField(default=0)
	loc_per_h 	= models.BooleanField(default=True)
	members		= models.ManyToManyField(User, related_name="Project Members")
	active		= models.BooleanField(default=True)
	tags		= models.ManyToManyField('Tag', related_name="Project Tags")

	def __str__(self):
		return self.name +" (manager: " + self.manager.__str__() + ")"

class Worklog(models.Model):
	"""
	Defines a model that contains data for work logged 
	on a Project.
	"""
	project 	= models.ForeignKey(Project)
	owner 		= models.ForeignKey(User)
	summary 	= models.CharField(max_length=140)
	description = models.CharField(max_length=300)
	hours 		= models.IntegerField(default=0)
	minutes 	= models.IntegerField(default=0)
	datestamp 	= models.DateTimeField(auto_now=False, auto_now_add=True)

	def __str__(self):
		return self.project.__str__() +" log (" +str(self.datestamp)+" )"


class ProjectTask(models.Model):
	"""
	Defines a task (which may or may not be associated 
	with a project).
	"""
	assigned 	= models.ManyToManyField(User, related_name="Assigned Members")
	creator 	= models.ForeignKey(User, related_name="Creator")
	summary		= models.CharField(max_length=100)
	description	= models.CharField(max_length=400)
	completed	= models.BooleanField(default=False)
	startDate	= models.DateTimeField(auto_now=False, auto_now_add=True)
	dueDate		= models.DateTimeField(auto_now=False, auto_now_add=True)
	inProgress	= models.BooleanField(default=False)
	completed	= models.BooleanField(default=False)
	tags		= models.ManyToManyField('Tag', related_name="Task Tags")
	project 	= models.ForeignKey(Project, related_name="Project", null=True)


	def __str__(self):
		return "Task " + str( self.summary )

class Tag(models.Model):
	"""
	Defines a Tag, which can be associated with Projects and 
	ProjectTasks in order to better classify projects and tasks 
	and provide a method of filtering views.
	"""
	owner 		= models.ForeignKey(User, related_name="Owner" )
	name 		= models.CharField(max_length=100)
	description = models.CharField(max_length=255)
	active 		= models.BooleanField(default=True)
	public		= models.BooleanField(default=False)
	users 		= models.ManyToManyField(User, related_name="Tag users")
	viewers		= models.ManyToManyField(User, related_name="Tag viewers")
	usage 		= models.CharField(max_length=100)
	visible		= models.BooleanField(default=True)
	system		= models.CharField(max_length=100, default="")

	def __str__(self):
		return "Tag " + self.name + ": " + str(self.owner)

