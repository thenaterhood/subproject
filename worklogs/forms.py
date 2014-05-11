from django import forms

from worklogs.models import Worklog
from worklogs.models import WorklogPrefs


class EditWorklogForm(forms.ModelForm):

    """
    Defines a form for creating and updating worklogs.
    """
    summary = forms.CharField(widget=forms.TextInput(
        attrs={"required": True, "max_length": 140, "placeholder": "Work Summary", 'class': 'form-control'}), label=(""))
    description = forms.CharField(widget=forms.Textarea(
        attrs={"required": False, "max_length": 300, "placeholder": "Work Description", 'class': 'form-control'}), label=(""))
    hours = forms.DecimalField(widget=forms.TextInput(
        attrs={"required": True, "max_length": 5, "placeholder": "Hours Spent", 'class': 'form-control'}), label=(""))
    minutes = forms.DecimalField(widget=forms.TextInput(
        attrs={"required": True, "max_length": 2, "placeholder": "Minutes Spent", 'class': 'form-control'}), label=(""))

    class Meta:
        model = Worklog
        fields = ('summary', 'description', 'hours', 'minutes')

    def save(self, owner=False, project=False, commit=True):
        newLog = super(EditWorklogForm, self).save(commit=False)

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

class EditSettingsForm(forms.ModelForm):
    public = forms.BooleanField(help_text="Make your worklogs visible to the public.",widget=forms.CheckboxInput(
      attrs={'class': 'form-control', 'title': 'Make your worklogs visible to the public.'}))

    class Meta:
      model = WorklogPrefs
      fields = ('public',)
