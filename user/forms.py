from django import forms #bring in the forms framework
from django.contrib.auth.models import User #needed to fill in User information records and save them
from django.contrib.auth.forms import UserCreationForm #used so we can inherit this in our new class
import re
from django.utils.translation import ugettext_lazy as _

class UserRegistrationForm(UserCreationForm):
	"""
	Defines the first part of the user registration form.
	"""
	email = forms.EmailField(required=True) #creates an email field that is required
	first_name = forms.CharField(widget=forms.TextInput(attrs=dict(required=True, max_length=30, placeholder="First Name")), label=(""))
	last_name = forms.CharField(widget=forms.TextInput(attrs=dict(required=True, max_length=30, placeholder="Last Name")), label=(""))
	username = forms.CharField(widget=forms.TextInput(attrs=dict(required=True, max_length=10, placeholder="Username")), label=(""))
	email = forms.EmailField(widget=forms.TextInput(attrs=dict(required=True, max_length=30, placeholder="Email")), label=(""))
	password1 = forms.CharField(widget=forms.PasswordInput(attrs=dict(required=False, max_length=30, render_value=False, placeholder="Password")), label=(""))
	password2 = forms.CharField(widget=forms.PasswordInput(attrs=dict(required=False, max_length=30, render_value=False, placeholder="Confirm Password")), label=(""))

	class Meta: #inner class -> holds anything that isn't a form field -> metadata for the class itself
		model = User
		fields = ('first_name', 'last_name', 'username', 'email', 'password1', 'password2')

	def save(self, commit=True):
		"""
		Saves the information included in the above form

		Returns:
			user - An updated/saved django user instance
		"""

		user = super(UserRegistrationForm, self).save(commit=False)
		user.email = self.cleaned_data['email']
		user.set_password(self.cleaned_data['password1'])

		if commit:
			user.save()

		return user