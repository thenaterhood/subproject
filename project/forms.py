from django import forms #bring in the forms framework
from django.contrib.auth.models import User #needed to fill in User information records and save them
from django.contrib.auth.forms import UserCreationForm #used so we can inherit this in our new class
import re
from django.utils.translation import ugettext_lazy as _

from project.models import *

class EditProjectForm(forms.ModelForm):
	"""
	Defines a form for creating and updating Projects.
	"""
	name = forms.CharField(widget=forms.TextInput(attrs={"required":True, "max_length":50, "placeholder":"Project Name", "class":'form-control'}), label=(""))
	status = forms.CharField(widget=forms.TextInput(attrs={"required":True, "max_length":50, "placeholder":"Project Status", 'class':'form-control'}), label=(""))
	phase = forms.CharField(widget=forms.TextInput(attrs={"required":True, "max_length":50, "placeholder":"Project Phase", 'class':'form-control'}), label=(""))
	description = forms.CharField(widget=forms.Textarea(attrs={"required":True, "max_length":140, "placeholder":"Project Description in 140 Characters", 'class':'form-control'}), label=(""))

	class Meta:
		model = Project
		fields = ('name', 'status', 'phase', 'description')

	def save(self, owner=False, commit=True):
		"""
		Saves the updated model.

		Arguments:
			owner - User project manager
			commit - Commit to the database (default: True)
		"""
		newProject = super( EditProjectForm, self ).save(commit=False)

		if owner:
			newProject.manager = owner
		elif newProject.manager is None:
			raise Exception('No project owner provided.')
		else:
			pass

		if commit:
			newProject.save()

		newProject.members.add( owner )

		return newProject


class EditWorklogForm(forms.ModelForm):
	"""
	Defines a form for creating and updating worklogs.
	"""
	summary = forms.CharField(widget=forms.TextInput(attrs={"required":True, "max_length":140, "placeholder":"Work Summary", 'class':'form-control'}),label=(""))
	description = forms.CharField(widget=forms.Textarea(attrs={"required":False, "max_length":300, "placeholder":"Work Description", 'class':'form-control'}), label=(""))
	hours = forms.DecimalField(widget=forms.TextInput(attrs={"required":True, "max_length":5, "placeholder":"Hours Spent", 'class':'form-control'}), label=(""))
	minutes = forms.DecimalField(widget=forms.TextInput(attrs={"required":True, "max_length":2, "placeholder":"Minutes Spent", 'class':'form-control'}), label=(""))



	class Meta:
		model = Worklog
		fields = ('summary', 'description', 'hours', 'minutes')


	def save(self, owner=False, project=False, commit=True):
		newLog = super( EditWorklogForm, self ).save(commit=False)

		if owner:
			newLog.owner = owner
		elif newLog.owner is None:
			raise Exception('No owner specified for worklog.')
		else:
			pass

		if project:
			newLog.project = project
		elif newLog.project is None:
			raise Exception('No project specified for worklog.')
		else:
			pass

		if commit:
			newLog.save()

		return newLog
		

class AddMemberForm(forms.Form):
	"""
	Defines a form for entering a username of a site 
	member.
	"""
	username = forms.CharField(widget=forms.TextInput(attrs={"required":True, "max_length":50, "placeholder":"Add Member", 'class':'form-control'}), label=(""))

	class Meta:
		fields = ('username')


class EditTaskForm(forms.ModelForm):
	"""
	Defines a form for creating and editing task 
	objects.
	"""
	summary = forms.CharField(widget=forms.TextInput(attrs={"required":True, "max_length":140, "placeholder":"Task Summary", 'class':'form-control'}),label=(""))
	description = forms.CharField(widget=forms.Textarea(attrs={"required":False, "max_length":300, "placeholder":"Task Description", 'class':'form-control'}), label=(""))

	class Meta:
		model = ProjectTask
		fields = ('summary', 'description')

	def save(self, owner=False, commit=True):
		newTask = super( EditTaskForm, self ).save(commit=False)

		if newTask.creator is None:
			if owner:
				newTask.creator = owner
			else:
				raise Exception('No owner specified for project task.')

		if commit:
			newTask.save()

		return newTask


class AddTagForm(forms.ModelForm):
	"""
	Defines a form for creating and updating 
	tags.
	"""
	name = forms.CharField(widget=forms.TextInput(attrs={"required":True, "max_length":100, "placeholder":"Tag Name", 'class':'form-control'}),label=(""))
	public = forms.BooleanField(widget=forms.CheckboxInput(attrs={'class':'form-control', 'title':'Make this tag publicly visible.'}))
	description = forms.CharField(widget=forms.Textarea(attrs={"required":True, "max_length":255, "placeholder":"Tag Description", 'class':'form-control'}),label=(""))


	class Meta:
		model = Tag
		fields = ('name', 'description', 'public')

class UploadFileForm(forms.Form):
    file  = forms.FileField()