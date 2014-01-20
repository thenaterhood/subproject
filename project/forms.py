from django import forms #bring in the forms framework
from django.contrib.auth.models import User #needed to fill in User information records and save them
from django.contrib.auth.forms import UserCreationForm #used so we can inherit this in our new class
import re
from django.utils.translation import ugettext_lazy as _

from project.models import *

class CreateProjectForm(forms.ModelForm):

	name = forms.CharField(widget=forms.TextInput(attrs={"required":True, "max_length":50, "placeholder":"Project Name", "class":'form-control'}), label=(""))
	status = forms.CharField(widget=forms.TextInput(attrs={"required":True, "max_length":50, "placeholder":"Project Status", 'class':'form-control'}), label=(""))
	phase = forms.CharField(widget=forms.TextInput(attrs={"required":True, "max_length":50, "placeholder":"Project Phase", 'class':'form-control'}), label=(""))
	description = forms.CharField(widget=forms.Textarea(attrs={"required":True, "max_length":140, "placeholder":"Project Description in 140 Characters", 'class':'form-control'}), label=(""))

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

	name = forms.CharField(widget=forms.TextInput(attrs={"required":True, "max_length":50, "placeholder":"Project Name", 'class':'form-control'}), label=(""))
	status = forms.CharField(widget=forms.TextInput(attrs={"required":False, "max_length":50, "placeholder":"Project Status", 'class':'form-control'}), label=(""))
	phase = forms.CharField(widget=forms.TextInput(attrs={"required":False, "max_length":50, "placeholder":"Project Phase", 'class':'form-control'}), label=(""))
	lines = forms.DecimalField(widget=forms.TextInput(attrs={"required":False, "max_length":50, "placeholder":"Lines of Code", 'class':'form-control'}), label=(""))
	description = forms.CharField(widget=forms.Textarea(attrs={"required":True, "max_length":140, "placeholder":"Project Description in 140 Characters", 'class':"form-control"}), label=(""))

	class Meta:
		model = Project
		fields = ('name', 'status', 'phase', 'description', 'lines')

class AddWorklogForm(forms.ModelForm):

	summary = forms.CharField(widget=forms.Textarea(attrs={"required":True, "max_length":140, "placeholder":"Work Summary", 'class':'form-control'}),label=(""))
	description = forms.CharField(widget=forms.Textarea(attrs={"required":False, "max_length":300, "placeholder":"Work Description", 'class':'form-control'}), label=(""))
	hours = forms.DecimalField(widget=forms.TextInput(attrs={"required":True, "max_length":5, "placeholder":"Hours Spent", 'class':'form-control'}), label=(""))
	minutes = forms.DecimalField(widget=forms.TextInput(attrs={"required":True, "max_length":5, "placeholder":"Minutes Spent", 'class':'form-control'}), label=(""))

	class Meta:
		model = Worklog
		fields = ('summary', 'description', 'hours', 'minutes' )


class UpdateWorklogForm(forms.ModelForm):

	summary = forms.CharField(widget=forms.Textarea(attrs={"required":True, "max_length":140, "placeholder":"Work Summary", 'class':'form-control'}),label=(""))
	description = forms.CharField(widget=forms.Textarea(attrs={"required":False, "max_length":300, "placeholder":"Work Description", 'class':'form-control'}), label=(""))
	hours = forms.DecimalField(widget=forms.TextInput(attrs={"required":True, "max_length":5, "placeholder":"Hours Spent", 'class':'form-control'}), label=(""))
	minutes = forms.DecimalField(widget=forms.TextInput(attrs={"required":True, "max_length":5, "placeholder":"Minutes Spent", 'class':'form-control'}), label=(""))


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

	username = forms.CharField(widget=forms.TextInput(attrs={"required":True, "max_length":50, "placeholder":"Add Member", 'class':'form-control'}), label=(""))

	class Meta:
		fields = ('username')

class AddTaskForm(forms.ModelForm):

	summary = forms.CharField(widget=forms.TextInput(attrs={"required":True, "max_length":140, "placeholder":"Task Summary", 'class':'form-control'}),label=(""))
	description = forms.CharField(widget=forms.Textarea(attrs={"required":False, "max_length":300, "placeholder":"Task Description", 'class':'form-control'}), label=(""))

	class Meta:
		model = ProjectTask
		fields = ('summary', 'description')

class UpdateTaskForm(forms.ModelForm):

	summary = forms.CharField(widget=forms.TextInput(attrs={"required":True, "max_length":140, "placeholder":"Task Summary", 'class':'form-control'}),label=(""))
	description = forms.CharField(widget=forms.Textarea(attrs={"required":False, "max_length":300, "placeholder":"Task Description", 'class':'form-control'}), label=(""))

	class Meta:
		model = ProjectTask
		fields = ('summary', 'description')

	def save(self, commit=True):
		newTask = super( AddTaskForm, self ).save(commit=False)

		newTask.summary = self.cleaned_data['summary']
		newTask.description = self.cleaned_data['description']

class AddTagForm(forms.ModelForm):

	name = forms.CharField(widget=forms.TextInput(attrs={"required":True, "max_length":100, "placeholder":"Tag Name", 'class':'form-control'}),label=(""))
	public = forms.BooleanField(widget=forms.CheckboxInput(attrs={'class':'form-control', 'title':'Make this tag publicly visible.'}))
	description = forms.CharField(widget=forms.Textarea(attrs={"required":True, "max_length":255, "placeholder":"Tag Description", 'class':'form-control'}),label=(""))


	class Meta:
		model = Tag
		fields = ('name', 'description', 'public')