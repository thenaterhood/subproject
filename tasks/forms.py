from django import forms #bring in the forms framework
from django.contrib.auth.models import User #needed to fill in User information records and save them
from django.contrib.auth.forms import UserCreationForm #used so we can inherit this in our new class
import re
from django.utils.translation import ugettext_lazy as _

from tasks.models import ProjectTask

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