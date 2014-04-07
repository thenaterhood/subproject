from django import forms
from django.contrib.auth.models import User

from tasks.models import ProjectTask


class EditTaskForm(forms.ModelForm):

    """
    Defines a form for creating and editing task 
    objects.
    """
    summary = forms.CharField(widget=forms.TextInput(
        attrs={"required": True, "max_length": 140, "placeholder": "Task Summary", 'class': 'form-control'}), label=(""))
    description = forms.CharField(widget=forms.Textarea(
        attrs={"required": False, "max_length": 300, "placeholder": "Task Description", 'class': 'form-control'}), label=(""))

    class Meta:
        model = ProjectTask
        fields = ('summary', 'description')

    def save(self, owner=False, commit=True):
        newTask = super(EditTaskForm, self).save(commit=False)

        if newTask.creator is None:
            if owner:
                newTask.creator = owner
            else:
                raise Exception('No owner specified for project task.')

        if commit:
            newTask.save()

        return newTask
