from django import forms #bring in the forms framework
from django.contrib.auth.models import User #needed to fill in User information records and save them
from django.contrib.auth.forms import UserCreationForm #used so we can inherit this in our new class
import re
from django.utils.translation import ugettext_lazy as _

from worklogs.models import Worklog

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
