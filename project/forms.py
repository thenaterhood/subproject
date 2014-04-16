from django import forms  # bring in the forms framework
# needed to fill in User information records and save them
from django.contrib.auth.models import User
# used so we can inherit this in our new class
from django.contrib.auth.forms import UserCreationForm
import re
from django.utils.translation import ugettext_lazy as _

from project.models import *


class EditProjectForm(forms.ModelForm):

    """
    Defines a form for creating and updating Projects.
    """
    name = forms.CharField(widget=forms.TextInput(
        attrs={"required": True, "max_length": 50, "placeholder": "Project Name", "class": 'form-control'}), label=(""))
    status = forms.CharField(widget=forms.TextInput(
        attrs={"required": True, "max_length": 50, "placeholder": "Project Status", 'class': 'form-control'}), label=(""))
    phase = forms.CharField(widget=forms.TextInput(
        attrs={"required": True, "max_length": 50, "placeholder": "Project Phase", 'class': 'form-control'}), label=(""))
    description = forms.CharField(widget=forms.Textarea(
        attrs={"required": True, "max_length": 140, "placeholder": "Project Description in 140 Characters", 'class': 'form-control'}), label=(""))
    public = forms.BooleanField(widget=forms.CheckboxInput(
        attrs={'class': 'form-control', 'title': 'Make this project publicly visible.'}))

    class Meta:
        model = Project
        fields = ('name', 'status', 'phase', 'description', 'public')

    def save(self, owner=False, commit=True):
        """
        Saves the updated model.

        Arguments:
                owner - User project manager
                commit - Commit to the database (default: True)
        """
        newProject = super(EditProjectForm, self).save(commit=False)

        if owner:
            newProject.manager = owner
        elif newProject.manager is None:
            raise Exception('No project owner provided.')
        else:
            pass

        if commit:
            newProject.save()

        newProject.members.add(owner)

        return newProject


class UploadFileForm(forms.Form):
    file = forms.FileField()
