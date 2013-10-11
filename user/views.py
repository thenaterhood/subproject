from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.contrib import auth
from django.core.context_processors import csrf
from django.template import RequestContext
from django.contrib.auth.decorators import login_required

from user.forms import * #all forms
from user.models import *

# Create your views here.
def register_user(request):
	"""
	Defines the request to response of the user registration page

	Returns:
		either the same page or a rendered page of register.html
	"""
	if request.method == 'POST': #see if the method of the request objerct 'POST' -> first time it should be no, second time yes
		form = UserRegistrationForm(request.POST) #pass the values from POST dictionary into the MyRegistrationForm and create form object

		if form.is_valid(): #is the form valid (info is correct)
			user = form.save(commit=False) #save the form, save the registration information for the new user
			servUser = ServiceUser()
			user.save()
			servUser.auth = user

			servUser.save()
			return HttpResponseRedirect('/user/login/')

	#what happens the first time the user visits the register page

	args = {} #set up blank dictionary 
	args.update(csrf(request)) #pass through the csrf token
	args['form'] = UserRegistrationForm() #blank MyRegistrationForm, no POST data in arguement, render the forms fields as blank
	return render_to_response('user_register.html', args) #pass the form to the register.html template

def login_user(request):
	"""
	Defines the request to response of the functionality of login

	Returns:
		A rendered page of login.html
	"""

	c = {}
	c.update(csrf(request))
	return render_to_response('user_login.html', c)

def auth_user(request):
	"""
	Defines an intermediate step/page that checks the validity of a user

	Returns:
		A redirect to the loggin success page or the user invalid page
	"""

	username = request.POST.get('username', '') #blank string means if you can't find a value, use a blank string
	password = request.POST.get('password', '')
	user = auth.authenticate(username=username, password=password) #assigns a user obj to 'user' if it exists, otherwise return 'None'

	if user is not None: #if we found a user that authenticates
		auth.login(request, user) #signify the user as logged in
		return HttpResponseRedirect('/user/welcome') #redirect them to the loggedin page
	else:
		return HttpResponseRedirect('/user/login') #redirect them to the invalid login page

@login_required
def welcome(request):

	return render_to_response('user_welcome.html',{'full_name' : request.user.username})

def logout(request):
	"""
	Defines the request to response of logout page returning back to the
	login page

	Returns:
		A rendered page of login.html
	"""
	c = {}
	c.update(csrf(request))
	auth.logout(request) #use auth to logout the user
	return render_to_response('user_login.html',c)