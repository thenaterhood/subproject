from django import forms #bring in the forms framework
from django.contrib.auth.models import User #needed to fill in User information records and save them
from django.contrib.auth.forms import UserCreationForm #used so we can inherit this in our new class
import re
from django.utils.translation import ugettext_lazy as _

from project.models import *

class CreateProjectForm(forms.ModelForm):

	name = forms.CharField(widget=forms.TextInput(attrs=dict(required=True, max_length=50, placeholder="Project Name")), label=(""))
	status = forms.CharField(widget=forms.TextInput(attrs=dict(required=True, max_length=50, placeholder="Project Status")), label=(""))
	phase = forms.CharField(widget=forms.TextInput(attrs=dict(required=True, max_length=50, placeholder="Project Phase")), label=(""))
	description = forms.CharField(widget=forms.Textarea(attrs=dict(required=True, max_length=140, placeholder="Project Description in 140 Characters")), label=(""))

	class Meta:
		model = Project
		fields = ('name', 'status', 'phase', 'description')

	def save(self, commit=True):
		newProject = super( CreateProjectForm, self ).save(commit=False)

		newProject.name = self.cleaned_data['name']
		newProject.status = self.cleaned_data['status']
		newProject.phase = self.cleaned_data['phase']
		newProject.description = self.cleaned_data['description']

class UpdateProjectForm(forms.ModelForm):

	name = forms.CharField(widget=forms.TextInput(attrs=dict(required=True, max_length=50, placeholder="Project Name")), label=(""))
	status = forms.CharField(widget=forms.TextInput(attrs=dict(required=True, max_length=50, placeholder="Project Status")), label=(""))
	phase = forms.CharField(widget=forms.TextInput(attrs=dict(required=True, max_length=50, placeholder="Project Phase")), label=(""))
	lines = forms.DecimalField(widget=forms.TextInput(attrs=dict(required=True,max_length=50, placeholder="Lines of Code")), label=(""))
	description = forms.CharField(widget=forms.Textarea(attrs=dict(required=True, max_length=140, placeholder="Project Description in 140 Characters")), label=(""))

	class Meta:
		model = Project
		fields = ('name', 'status', 'phase', 'description', 'lines')

class AddWorklogForm(forms.ModelForm):

	summary = forms.CharField(widget=forms.Textarea(attrs=dict(required=True, max_length=140, placeholder="Work Summary")),label=(""))
	description = forms.CharField(widget=forms.Textarea(attrs=dict(required=False, max_length=300, placeholder="Work Description")), label=(""))
	hours = forms.DecimalField(widget=forms.TextInput(attrs=dict(required=True, max_length=5, placeholder="Hours Spent")), label=(""))
	minutes = forms.DecimalField(widget=forms.TextInput(attrs=dict(required=True, max_length=5, placeholder="Minutes Spent")), label=(""))
	taskClosed = forms.ChoiceField(choices=[], label=("Close a task"))

	class Meta:
		model = Worklog
		fields = ('summary', 'description', 'hours', 'minutes' )

	def updateChoices( self, choices ):

		self.fields['taskClosed'] = forms.ChoiceField(widget=forms.Select(attrs=dict(required=True)),
			choices=[('None','Task Completed (None)')]+[(str(x.id), x.summary) for x in choices])


class UpdateWorklogForm(forms.ModelForm):

	summary = forms.CharField(widget=forms.Textarea(attrs=dict(required=True, max_length=140, placeholder="Work Summary")),label=(""))
	description = forms.CharField(widget=forms.Textarea(attrs=dict(required=False, max_length=300, placeholder="Work Description")), label=(""))
	hours = forms.DecimalField(widget=forms.TextInput(attrs=dict(required=True, max_length=5, placeholder="Hours Spent")), label=(""))
	minutes = forms.DecimalField(widget=forms.TextInput(attrs=dict(required=True, max_length=5, placeholder="Minutes Spent")), label=(""))


	class Meta:
		model = Worklog
		fields = ('summary', 'description', 'hours', 'minutes')

	def save(self, commit=True):
		newLog = super( AddWorklogForm, self ).save(commit=False)

		newLog.summary = self.cleaned_data['summary']
		newLog.description = self.cleaned_data['description']
		newLog.hours = self.cleaned_data['hours']
		newLog.minutes = self.cleaned_data['minutes']

class AddMemberForm(forms.Form):

	username = forms.CharField(widget=forms.TextInput(attrs=dict(required=True, max_length=50, placeholder="Add Member")), label=(""))

	class Meta:
		fields = ('username')

class AddTaskForm(forms.ModelForm):

	summary = forms.CharField(widget=forms.Textarea(attrs=dict(required=True, max_length=140, placeholder="Task Summary")),label=(""))
	description = forms.CharField(widget=forms.Textarea(attrs=dict(required=False, max_length=300, placeholder="Task Description")), label=(""))

	class Meta:
		model = ProjectTask
		fields = ('summary', 'description')

class UpdateTaskForm(forms.ModelForm):

	summary = forms.CharField(widget=forms.Textarea(attrs=dict(required=True, max_length=140, placeholder="Task Summary")),label=(""))
	description = forms.CharField(widget=forms.Textarea(attrs=dict(required=False, max_length=300, placeholder="Task Description")), label=(""))

	class Meta:
		model = ProjectTask
		fields = ('summary', 'description')

	def save(self, commit=True):
		newTask = super( AddTaskForm, self ).save(commit=False)

		newTask.summary = self.cleaned_data['summary']
		newTask.description = self.cleaned_data['description']
