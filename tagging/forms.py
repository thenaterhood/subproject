from django import forms  # bring in the forms framework
import re
from django.utils.translation import ugettext_lazy as _

from tagging.models import Tag


class AddTagForm(forms.ModelForm):

    """
    Defines a form for creating and updating 
    tags.
    """
    name = forms.CharField(widget=forms.TextInput(
        attrs={"required": True, "max_length": 100, "placeholder": "Tag Name", 'class': 'form-control'}), label=(""))
    public = forms.BooleanField(widget=forms.CheckboxInput(
        attrs={'class': 'form-control', 'title': 'Make this tag publicly visible.'}))
    description = forms.CharField(widget=forms.Textarea(
        attrs={"required": True, "max_length": 255, "placeholder": "Tag Description", 'class': 'form-control'}), label=(""))

    class Meta:
        model = Tag
        fields = ('name', 'description', 'public')
