from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.contrib import auth
from django.core.context_processors import csrf
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import F
from django.db.models import Q
from django.db.models import Count
from django.contrib import messages

from copy import deepcopy

from project.models import *
from project.forms import *
from project.filters import reset_filter, apply_task_filter, apply_project_filter, set_filter_message

import project.thenaterhood.histogram as histogram

def ensure_userstat_exists( user ):
	"""
	Ensures that a user has an existing 
	userstatistic object.
	"""

	try:
		UserStatistic.objects.get(user=user)
	except:
		
		userStat = UserStatistic()
		userStat.user = user

		userStat.save()


@login_required
def project_welcome(request):
	"""
	Renders the project dashboard with 
	basic user statistics.
	"""

	ensure_userstat_exists( request.user )

	# Assemble a collection of statistics to render to the template
	args = {}
	messages.warning( request, "This app is in what could be considered alpha stage. Don't store anything \
		important on it as it will not be up reliably and the database may be cleared periodically as more \
		development goes on. Right now it supports logging tasks completed on projects and adding/removing \
		project collaborators. There's more to come and the UI is not final. ")
	userStats = UserStatistic.objects.get( user=request.user )
	args['total_projects'] = len( Project.objects.filter(members=request.user) )
	args['managed_projects'] = len( Project.objects.filter(manager=request.user) )
	args['total_worklogs'] = userStats.worklogs
	args['total_tasks'] = ProjectTask.objects.filter( creator=request.user ).count()
	args['active_tasks'] = ProjectTask.objects.filter( creator=request.user ).filter( inProgress=True ).count()
	tasks = Worklog.objects.filter(owner=request.user).reverse()
	args['total_time'] = str( userStats.loggedTime / 60 )
	args['start_date'] = userStats.startDate
	args['end_date'] = userStats.endDate
	args['tasks'] = tasks[:5]
	args['numTasks'] = len(	ProjectTask.objects.filter( assigned=request.user ).annotate(c=Count('openOn')).filter(c__gt=0).all())

	args['avg_task_time'] = 0
	if ( userStats.worklogs > 0 ):
		args['avg_task_time'] = str( (userStats.loggedTime/60) / userStats.worklogs )

	return render_to_response('project_welcome.html', RequestContext( request, args) )

@login_required
def user_all_tasks(request):
	"""
	Displays all of the tasks created by the 
	logged in user
	"""

	tasks = apply_task_filter( request, ProjectTask.objects.filter( creator=request.user ) )
	set_filter_message( request )

	args = {}
	args['user'] = request.user
	args['tasks'] = tasks.filter( inProgress=False ).all()
	args['other_num'] = len( args['tasks'] )
	args['task_wip'] = tasks.filter( inProgress=True ).all()
	args['wip_num'] = len( args['task_wip'] )
	args['num_tasks'] = len(tasks)
	args['notodo'] = True

	return render_to_response( 'user_todo.html', RequestContext(request, args) )


@login_required
def list_projects(request):
	"""
	Displays a list of all the projects a user 
	is associated with.
	"""

	ensure_userstat_exists( request.user )

	projects = apply_project_filter(request, Project.objects.filter(members=request.user) )
	set_filter_message( request )
	managedProjects = Project.objects.filter(manager=request.user)

	args = {}
	args['projects'] = projects
	args['owned'] = managedProjects
	args['num_projects'] = len(projects)

	return render_to_response('project_list.html', RequestContext( request, args) )

@login_required
def create_project(request, parent=False):
	"""
	Provides a new project form and adds 
	a project to the database after verifying 
	the data.
	"""

	if request.method == "POST":

		if ( not request.POST['returnUrl'] ):
			redirTo = '/projects/'
		else:
			redirTo = request.POST['returnUrl']

		newProj = Project()
		newStat = ProjectStatistic()
		form = EditProjectForm(request.POST)
		if form.is_valid() and not "useexisting" in request.POST:

			newProj = form.save( owner=request.user )
			newStat.project = newProj

			if ( request.POST['parent'] != "False" ):
				parentProject = Project.objects.get( id=request.POST['parent'] )

				newProj.parents.add(parentProject)
				parentProject.subprojects.add(newProj)
				parentProject.save()

			newStat.save()

			newProj.save()

			return HttpResponseRedirect(redirTo)

		elif "useexisting" in request.POST:
			request.session['returnUrl'] = request.POST['returnUrl']
			return HttpResponseRedirect('/projects/'+str(request.POST['parent'])+'/assignchild')

		else:

			pageData = {}
			pageData['form'] = EditProjectForm( request.POST )
			messages.warning( request, "Please check your input, all fields are required." )
			return render_to_response( 'project_create.html', RequestContext( request, pageData) )


	else:

		args = {}
		args.update(csrf(request))
		try:
			args['returnUrl'] = request.META['HTTP_REFERER']
		except:
			args['returnUrl'] = '/projects/'
		args['addingSub'] = parent
		args['form'] = EditProjectForm()
		args['parent'] = parent
		return render_to_response('project_create.html', args)

def assign_child( request, parent_id, child_id=False ):
	"""
	Assigns a new subproject to a project.

	Arguments:
		parent_id - integer ID of the parent project
		child_id - integer ID of the to-be child project (
			false triggers displaying the selection page)

	Returns:
		The rendered selection page or a redirect back to the 
		original page.
	"""
	if ( child_id ):

		try:
			parent = Project.objects.get( id=parent_id )
			child = Project.objects.get( id=child_id )

			parent.subprojects.add( child )
			child.parents.add( parent )

			parent.save()
			child.save()

			if ( "returnUrl" in request.session ):
				returnUrl = request.session['returnUrl']
				del request.session['returnUrl']
				return HttpResponseRedirect( returnUrl )
			else:
				return HttpResponseRedirect( '/projects/view/'+str(parent_id) )

		except:
			return HttpResponseRedirect( '/projects/' )

	else:
		pageData = {}
		parentProj = Project.objects.get( id=parent_id )
		pageData['projects'] = Project.objects.filter( manager=request.user ).exclude( id=parent_id ).exclude( parents=parentProj )
		return render_to_response( 'project_select.html', RequestContext( request, pageData ) )

@login_required
def edit_project(request, proj_id):
	"""
	Retrieves a project and provides a populated form 
	for updating its information, as well as accepting 
	an updated version of the form.
	"""

	project = Project.objects.get(id=proj_id)

	if ( request.method == "POST" and project.manager == request.user ):
		form = EditProjectForm( request.POST, instance=project )
		if form.is_valid():
			form.save()

			return HttpResponseRedirect( '/projects/view/' + str(project.id) +"/" )

		else:
			pageData = {}
			pageData['form'] = EditProjectForm(request.POST, instance=project)
			messages.error( request, 'Please fill out all the fields.')

			return render_to_response('project_edit.html', RequestContext( request, pageData) )



	else:

		form = EditProjectForm(instance=project)

		args = {}
		args['form'] = form
		args.update(csrf(request))
		args['project'] = project

		return render_to_response('project_edit.html', args)

@login_required
def toggle_tag_viewer( request, tag_id, user_id=False ):
	"""
	Adds or removes a user's tag viewing rights for a 
	selected tag.

	Arguments:
		tag_id - integer tag to remove rights from
		user_id - integer user ID to remove from the tag viewers.
			False triggers a search in the POST array for a username.

	Returns:
		a redirect back to the page the request originated from.
	"""
	tag = Tag.objects.get( id=tag_id )

	if ( (request.user == tag.owner or request.user in tag.users.all() ) ):
		if ( not user_id ):
			form = AddMemberForm( request.POST )
			form.is_valid()
			user = User.objects.get( username=form.cleaned_data['username'] )
		else:
			user = User.objects.get( id=user_id )


		if ( user in tag.viewers.all() ):
			tag.viewers.remove( user )
		else:
			tag.viewers.add( user )

		tag.save()

	messages.info( request, "Updated " + str(user) + "'s tag viewer status." )
	return HttpResponseRedirect( '/projects/tags/' + str(tag_id) )


@login_required
def toggle_tag_user( request, tag_id, user_id=False ):
	"""
	Adds or removes a user's tag user rights for a 
	selected tag.

	Arguments:
		tag_id - integer tag to remove rights from
		user_id - integer user ID to remove from the tag viewers.
			False triggers a search in the POST array for a username.

	Returns:
		a redirect back to the page the request originated from.
	"""
	tag = Tag.objects.get( id=tag_id )

	if ( request.user == tag.owner or request.user in tag.users.all() ):
		
		if ( not user_id ):
			form = AddMemberForm( request.POST )
			form.is_valid()
			user = User.objects.get( username=form.cleaned_data['username'] )
		else:
			user = User.objects.get( id=user_id )

		if ( user in tag.users.all() ):
			tag.users.remove( user )
		else:
			tag.users.add( user )

		tag.save()

	messages.info( request, "Updated " + str(user) + "'s tag user status." )

	return HttpResponseRedirect( '/projects/tags/' + str(tag_id) )

@login_required
def delete_tag( request, tag_id ):
	"""
	Deletes a tag from the system.

	Arguments:
		tag_id - integer tag ID
	"""
	tag = Tag.objects.get( id=tag_id )
	if ( request.user == tag.owner ):
		tag.delete()

		messages.info( request, "Deleted tag " + tag.name )

	return HttpResponseRedirect( '/' )

@login_required
def view_tag( request, tag_id ):
	"""
	Displays a tag 
	"""
	tag = Tag.objects.get( id=tag_id )

	if ( request.user == tag.owner 
		or request.user in tag.viewers.all() 
		or request.user in tag.users.all() 
		or tag.public ):

		pageData = {}
		pageData['tag'] = tag
		pageData['canEdit'] = ( request.user == tag.owner or request.user in tag.users.all() )
		pageData['taggedProjects'] = Project.objects.filter( tags=tag )
		pageData['taggedTasks'] = ProjectTask.objects.filter( tags=tag )
		pageData['viewers'] = tag.viewers.all()
		pageData['users'] = tag.users.all()
		pageData['public'] = tag.public
		pageData['add_user_form'] = AddMemberForm()
		form = AddTagForm()
		initialDict = {
			'public': tag.public,
			'name' : tag.name,
			'description' : tag.description
		}
		form.initial = initialDict
		pageData['form'] = form

		return render_to_response('tag_view.html', RequestContext(request, pageData) )

	else:
		return HttpResponseRedirect( '/projects/mytags' )

@login_required
def add_tag( request, tag_id=False, project_id=False, task_id=False ):
	"""
	Provides a page where tags can be 
	created by the user.
	"""
	if request.method == 'POST':
		postData = deepcopy( request.POST )

		if ( 'public' not in request.POST ):
			postData['public'] = 'off'

		form = AddTagForm( postData )

		if form.is_valid():

			if ( not tag_id ):
				newTag = Tag()
			else:
				newTag = Tag.objects.get( id=tag_id )

			newTag.name = form.cleaned_data['name']
			newTag.description = form.cleaned_data['description']
			newTag.public = form.cleaned_data['public']
			newTag.owner = request.user

			if ( 'public' not in request.POST ):
				newTag.public = False

			newTag.save()

			if ( task_id ):
				task = ProjectTask.objects.get( id=task_id )
				task.tags.add( newTag )
				task.save()
			if ( project_id ):
				project = Project.objects.get( id=project_id )
				project.tags.add( newTag )
				project.save()

			if ( 'returnUrl' in request.session ):
				return HttpResponseRedirect( request.session['returnUrl'] )
			else:
				return HttpResponseRedirect( '/projects/tags/' + str(newTag.id) )


		else:

			pageData = {}
			pageData['form'] = form
			pageData['postTo'] = request.get_full_path()
			messages.warning( request, "Please check your inputs." )
			return render_to_response('tag_create.html', RequestContext(request, pageData))


	else:
		form = AddTagForm()
		args = {}
		args['form'] = form
		args['postTo'] = request.get_full_path()
		return render_to_response('tag_create.html', RequestContext(request, args))

@login_required
def list_tags( request ):
	"""
	Displays a list of the user's tags
	"""

	tags = Tag.objects.filter( Q(owner=request.user)|Q(users=request.user)|Q(viewers=request.user) )

	pageData = {}
	pageData['tags'] = tags
	pageData['user'] = request.user

	return render_to_response( 'tag_list.html', RequestContext(request, pageData))

@login_required
def view_project(request, proj_id):
	"""
	Displays a project's dashboard
	"""

	project = Project.objects.get(id=proj_id)
	worklogs = Worklog.objects.filter(project=project).all().reverse()
	tags = project.tags.all()

	if not project.active:
		messages.warning( request, "This project is closed. Work and tasks cannot be added to closed projects.")

	args = {}
	args['parents'] = project.parents.all()
	args['num_parents'] = args['parents'].count()
	args['project'] = project
	args['children'] = project.subprojects.all()
	args['num_children'] = args['children'].count()
	args['members'] = project.members.all()
	args['canEdit'] = ( project.manager == request.user )
	args['isMember'] = ( request.user in project.members.all() )
	args['num_members'] = project.members.all().count()
	args['worklogs'] = worklogs
	args['num_worklogs'] = worklogs.count()
	args['tasks'] = ProjectTask.objects.filter( Q(openOn=project)|Q(closedOn=project) ).reverse()
	args['num_tasks'] = args['tasks'].count()
	args['tags'] = project.tags.filter( Q(owner=request.user)|Q(users=request.user)|Q(viewers=request.user)|Q(public=True) )
	args['yourTags'] = args['tags'].filter(Q(owner=request.user)|Q(users=request.user)|Q(viewers=request.user))


	form = EditProjectForm(instance=project)

	args['form'] = form

	if ( project.manager == request.user ):
		args['add_member_form'] = AddMemberForm()

	return render_to_response('project_view.html', RequestContext(request, args) )

@login_required
def task_progress_toggle( request, task_id ):
	"""
	Toggles a task's in progress status

	Arguments:
		task_id: integer task ID to toggle
	"""
	task = ProjectTask.objects.get( id=task_id )

	if ( request.user in task.assigned.all() or request.user == task.creator ):
		task.inProgress = not task.inProgress
		task.save()

		messages.info( request, "Task Updated.")

	return HttpResponseRedirect(request.META['HTTP_REFERER'])

@login_required
def unassign_task_from_project( request, task_id, project_id ):
	"""
	Removes a task's association with a project.

	Arguments:
		task_id: integer task ID to remove from project
		project_id: integer project ID to remove task from

	Returns:
		a redirect back to the page the request originated on
	"""
	task = ProjectTask.objects.get( id=task_id )
	project = Project.objects.get( id=project_id )

	if ( request.user in project.members.all() or request.user == task.creator ):
		task.openOn.remove( project )
		task.closedOn.remove( project )
		task.save()

	return HttpResponseRedirect(request.META['HTTP_REFERER'])

@login_required
def add_member(request, proj_id):
	"""
	Adds a member to a project
	"""

	project = Project.objects.get(id=proj_id)

	if ( request.method == "POST" and project.manager == request.user ):
		form = AddMemberForm( request.POST )
		if ( form.is_valid() ):
			username = form.cleaned_data['username']

			try:
				user = User.objects.get(username=username)

				if ( user not in project.members.all() ):
					project.members.add( user )
					project.save()
					messages.info(request, "Assigned " +user.username+" to project.")
			except:
				messages.error( request, "User " + username + " is not a valid user.")


	return HttpResponseRedirect( '/projects/view/'+str(proj_id)+"/" )

@login_required
def remove_member( request, proj_id, user_id ):
	"""
	Removes a member from a project.
	"""
	project = Project.objects.get(id=proj_id)
	user = User.objects.get( id=user_id )

	if ( project.manager == request.user ):
		if ( user != project.manager ):
			project.members.remove( user )
			project.save()
			messages.info( request, "Removed " + user.username + " from project.")

	return HttpResponseRedirect( '/projects/view/'+str(proj_id)+"/" )

@login_required
def add_worklog( request, proj_id ):
	"""
	Provides a blank worklog form and accepts 
	the data from it.
	"""
	project = Project.objects.get(id=proj_id)
	args = {}
	args.update(csrf(request))
	args['project'] = project
	form = EditWorklogForm()
	args['form'] = form

	if (request.method == "POST") and (request.user in project.members.all() or request.user == project.manager):
		workLog = Worklog()

		form = EditWorklogForm(request.POST)

		if form.is_valid():

			workLog = form.save( owner=request.user, project=project )

			# Update the ProjectStatistic assoc with the project
			ProjectStatistic.objects.filter(project=project).update(worklogs=F("worklogs") + 1)
			ProjectStatistic.objects.filter(project=project).update(loggedTime=F("loggedTime") + (workLog.minutes + (workLog.hours * 60) ) )

			UserStatistic.objects.filter(user=request.user).update(worklogs=F("worklogs") + 1 )
			UserStatistic.objects.filter(user=request.user).update(loggedTime=F("loggedTime") + (workLog.minutes + (workLog.hours * 60) ) )

			messages.info( request, "Worklog saved successfully.")

			return HttpResponseRedirect('/projects/work/view/'+str(workLog.id)+"/")

		else:

			messages.error( request, "Form information is incorrect." )
			args['form'] = EditWorklogForm( request.POST )


			return render_to_response( 'worklog_create.html', RequestContext(request, args) )

	else:


		if request.user in project.members.all():

			return render_to_response('worklog_create.html', RequestContext(request, args) )

		else:

			return HttpResponseRedirect('/projects/')

@login_required
def view_worklog( request, log_id ):
	"""
	Displays the selected workLog
	"""
	worklog = Worklog.objects.get(id=log_id)

	initialDict = { 
		"summary": worklog.summary, 
		"minutes": worklog.minutes, 
		"hours": worklog.hours, 
		"description": worklog.description,
		}

	form = EditWorklogForm()
	form.initial = initialDict

	args = {}
	args['form'] = form
	args['worklog'] = worklog
	args['canEdit'] = ( request.user == worklog.owner )
	args['project'] = worklog.project

	return render_to_response('worklog_view.html', RequestContext(request, args) )

@login_required
def edit_worklog( request, log_id ):
	"""
	Displays a worklog's data and allows for it 
	to be edited and saved.
	"""
	worklog = Worklog.objects.get(id=log_id)
	projStat = ProjectStatistic.objects.get( project=worklog.project )

	if ( request.method == "POST" and worklog.owner == request.user ):
		form = EditWorklogForm( request.POST, instance=worklog )
		if form.is_valid():

			oldTime = worklog.minutes + (worklog.hours * 60)

			worklog = form.save()

			newTime = worklog.minutes + (worklog.hours * 60)

			logTimeChange = newTime - oldTime

			# Update the ProjectStatistic for the new time
			UserStatistic.objects.filter(user=worklog.owner).update(loggedTime=F("loggedTime") + logTimeChange )
			ProjectStatistic.objects.filter(project=worklog.project).update(loggedTime=F("loggedTime") + logTimeChange)

			messages.info( request, "Worklog updated.")

			return HttpResponseRedirect( '/projects/work/view/' + str(worklog.id) +"/" )

		else:
			messages.error( request, "Invalid form information.")
			pageData = {}
			pageData['form'] = EditWorklogForm( request.POST )

			return render_to_response( 'worklog_edit.html', RequestContext( request, pageData) )

	else:

		form = EditWorklogForm( instance=worklog )

		args = {}
		args['form'] = form
		args['worklog'] = worklog

		return render_to_response('worklog_edit.html', RequestContext( request, args) )

@login_required
def line_stats(request):
	"""
	Displays a histogram of the lines in the user's 
	projects.
	"""

	projects = Project.objects.filter(members=request.user)

	projectDict = {}

	for p in projects:
		projectDict[p.name] = p.lines

	hist = histogram.generateHistogram(projectDict)

	args = {}
	args['histogram'] = hist

	return render_to_response('project_stats_lines.html', args)

@login_required
def assign_task( request, proj_id, task_id=False ):
	"""
	Assigns a task to a project

	Arguments:
		task_id - integer task ID (initially false to 
			trigger selection page)
		proj_id - integer project ID

	Returns:
		rendered task selection template or redirect to 
		original page after selection.
	"""
	if ( task_id ):
		project = Project.objects.get( id=proj_id )
		task = ProjectTask.objects.get( id=task_id )

		task.openOn.add( project )
		task.save()

		if ( 'returnUrl' in request.session ):
			return HttpResponseRedirect( request.session['returnUrl'])
		else:
			return HttpResponseRedirect( '/projects/view/'+str(proj_id ) )

	else:
		pageData = {}
		project = Project.objects.get( id=proj_id )
		pageData['tasks'] = ProjectTask.objects.filter( creator=request.user ).exclude( openOn=project ).exclude( closedOn=project )

		return render_to_response('task_select.html', pageData)

@login_required
def assign_project_tag( request, proj_id, tag_id=False ):
	"""
	Adds a new or existing tag to a project.

	Arguments:
		proj_id: integer project ID
		tag_id: integer tag ID (initially false to trigger 
			selection)

	Returns:
		The rendered tag selection page or a redirect to the 
		initial URL the user arrived from.
	"""
	returnUrl = '/projects/view/' + str(proj_id)

	if not tag_id:
		tags = Tag.objects.filter( Q(owner=request.user) | Q(users=request.user) )
		project = Project.objects.get( id=proj_id )

		pageData = {}
		pageData['project'] = project
		pageData['tags'] = tags
		pageData['allowNew'] = True

		if ( 'HTTP_REFERER' in request.META ):
			request.session['returnUrl'] = request.META['HTTP_REFERER']

		return render_to_response( 'tag_select.html', RequestContext(request, pageData) )

	else:

		project = Project.objects.get( id=proj_id )
		tag = Tag.objects.get( id=tag_id )

		if ( request.user in tag.users.all() or request.user == tag.owner ):
			project.tags.add( tag )
			project.save()


		if ( 'returnUrl' in request.session ):
			returnUrl = request.session['returnUrl']

		return HttpResponseRedirect( returnUrl )

@login_required
def assign_task_tag( request, task_id, tag_id=False ):
	"""
	Adds an existing or new tag to an existing task.

	Arguments:
		task_id: integer task ID
		tag_id: integer tag ID (initially False to trigger
			selection page)

	Returns:
		a rendered tag selection page or a redirect to the 
		original page.
	"""
	returnUrl = '/projects/task/view/' + str(task_id)

	if not tag_id:
		tags = Tag.objects.filter( Q(owner=request.user) | Q(users=request.user) )
		task = ProjectTask.objects.get( id=task_id )

		pageData = {}
		pageData['task'] = task
		pageData['tags'] = tags
		pageData['allowNew'] = True


		return render_to_response( 'tag_select.html', RequestContext(request, pageData) )

	else:

		task = ProjectTask.objects.get( id=task_id )
		tag = Tag.objects.get( id=tag_id )

		if ( request.user in tag.users.all() or request.user == tag.owner ):

			task.tags.add( tag )
			task.save()


		return HttpResponseRedirect( returnUrl )



@login_required
def add_task( request, proj_id=False ):
	"""
	Provides a blank form for creating a new 
	task and the facilities for saving it and 
	redirecting to assign it to a project.
	"""

	if request.method == "POST" and "useexisting" not in request.POST:

		form = EditTaskForm(request.POST)
		if form.is_valid():

			projTask = form.save( owner=request.user )

			# Update the ProjectStatistic assoc with the project

			UserStatistic.objects.filter(user=request.user).update(issues=F("issues") + 1 )

			projTask.assigned.add( request.user )

			if proj_id != False:
				project = Project.objects.get(id=proj_id)

				if request.user in project.members.all():
					ProjectStatistic.objects.filter(project=project).update(issues=F("issues") + 1)
					projTask.openOn.add( project )
					projTask.save()
				else:
					messages.warning( request, "You do not have the rights to add tasks to " + project.name )

			messages.info( request, "Task Saved." )

			if ( "saveandassign" in request.POST ):
				return HttpResponseRedirect('/projects/addtotask/'+str(projTask.id)+"/" )
			else:
				if ( request.POST['returnUrl'] == '' ):
					return HttpResponseRedirect('/projects/task/view/'+str(projTask.id)+"/")
				else:
					return HttpResponseRedirect(request.POST['returnUrl'])

		else:
			messages.error( request, "Please fill out both fields." )

			pageData = {}
			pageData['form'] = EditTaskForm( request.POST )
			return render_to_response( 'task_create.html', RequestContext( request, pageData))

	elif "useexisting" in request.POST:

		if "returnUrl" in request.POST:
			request.session['returnUrl'] = request.POST['returnUrl']
		else:
			request.session['returnUrl'] = '/projects/view/'+str(proj_id)

		return HttpResponseRedirect('/projects/'+str(proj_id)+'/assigntask' )

	else:

		args = {}
		try:
			args['returnUrl'] = request.META['HTTP_REFERER']
		except:
			args['returnUrl'] = '/projects/usertasks'

		if ( proj_id != False ):
			args['project'] = project = Project.objects.get(id=proj_id)

		args['form'] = EditTaskForm()

		return render_to_response('task_create.html', RequestContext(request, args) )

@login_required
def delete_task(request, task_id):
	"""
	Deletes the selected task
	"""
	task = ProjectTask.objects.get(id=task_id)


	if ( request.user == task.creator ):
		task.delete()
		messages.info( request, "Deleted task." )
		return HttpResponseRedirect('/projects/usertasks/')

	else:
		messages.error( request, "You do not have the rights to delete this task." )
		return HttpResponseRedirect('/projects/task/view/'+str(task_id) )

@login_required
def untag_project( request, project_id, tag_id ):
	tag = Tag.objects.get( id=tag_id )
	project = Project.objects.get( id=project_id )

	if ( request.user in tag.users.all() or request.user == tag.owner ):
		project.tags.remove( tag )
		messages.info( request, "Untagged project " + project.name )

	else:
		messages.warning( request, "You are not allowed to remove this tag." )

	return HttpResponseRedirect( '/projects/view/' + str(project_id) )

@login_required
def untag_task( request, task_id, tag_id ):
	tag = Tag.objects.get( id=tag_id )
	task = ProjectTask.objects.get( id=task_id )

	if ( request.user in tag.users.all() or request.user == tag.owner ):
		task.tags.remove( tag )
		messages.info( request, "Untagged task " + task.summary )
	else:
		messages.warning( request, "You are not allowed to remove this tag. ")

	return HttpResponseRedirect( '/projects/task/view/' + str(task_id) )


@login_required
def view_task(request, task_id):
	"""
	Displays a chosen task
	"""

	task = ProjectTask.objects.get(id=task_id)
	projects = task.openOn.all()

	args = {}
	initialDict = { 
		"summary": task.summary, 
		"description": task.description,
		}

	form = EditTaskForm()
	form.initial = initialDict

	args['form'] = form
	args['openOn'] = task.openOn.all()
	args['closedOn'] = task.closedOn.all()
	args['task'] = task
	args['members'] = task.assigned.all()
	args['user'] = request.user
	args['canEdit'] = ( task.creator == request.user )
	args['isMember'] = ( request.user in task.assigned.all() )
	args['tags'] = task.tags.filter( Q(owner=request.user)|Q(users=request.user)|Q(viewers=request.user)|Q(public=True) )
	args['yourTags'] = args['tags'].filter(Q(owner=request.user)|Q(users=request.user)|Q(viewers=request.user))

	args.update(csrf(request))

	args['add_member_form'] = AddMemberForm()

	return render_to_response('task_view.html', RequestContext(request, args) )


@login_required
def toggle_project_task_status( request, project_id, task_id ):
	"""
	Toggles a task open or closed on a project

	Arguments:
		project_id - integer project id
		task_id - integer task id

	Returns:
		http redirect back to referring page or 
		the project view page if there isn't a referer 
	"""
	task = ProjectTask.objects.get( id=task_id )
	project = Project.objects.get( id=project_id )

	if ( request.user in task.assigned.all() or request.user == task.creator ) and ( request.user in project.members.all() ):
		if ( project in task.openOn.all() ):
			task.openOn.remove( project )
			task.closedOn.add( project )

		elif ( project in task.closedOn.all() ):
			task.openOn.add( project )
			task.closedOn.remove( project )

		else:
			task.openOn.add( project )

		messages.info( request, "Updated task on project." )

	try:
		return HttpResponseRedirect( request.META['HTTP_REFERER'] )
	except:
		return HttpResponseRedirect( '/projects/view/' + str(project_id) +'/' )



	


@login_required
def add_existing_task_to_project( request, task_id, project_id=False ):
	"""
	Associates an existing task with an additional project as 
	an open task on that project. Renders the project 
	selection template and accepts the project and task as GET 
	variables.

	Arguments:
		task_id - integer task id 
		project_id - integer project id: false for rendering 
			the initial selection page and true when the page returns 
			a selection from the user.

	Returns:
		the project selection page initially, then the project 
		view page after, if the user has permission to see it.
	"""

	task = ProjectTask.objects.get(id=task_id)

	if ( project_id != False ):
		project = Project.objects.get( id=project_id )

		if ( (request.user == task.creator and request.user == project.manager)
			or ( request.user in task.assigned.all() and request.user in project.members.all() )):

			task.openOn.add( project )
			task.save()

			return HttpResponseRedirect( '/projects/task/view/'+str(task_id)+"/" )

		else:
			return HttpResponseRedirect( '/projects/welcome' )

	else:

		args = {}
		args['task'] = task

		args['projects'] = Project.objects.filter( members=request.user )

		return render_to_response( 'project_select.html', args )




@login_required
def add_task_member(request, task_id):
	"""
	Adds a member (assignee) to a task

	Arguments:
		task_id - integer task ID
		user_id - integer user ID

	Returns:
		redirect back to the project view page 
	"""

	task = ProjectTask.objects.get(id=task_id)

	if ( request.method == "POST" and task.creator == request.user ):
		form = AddMemberForm( request.POST )
		if ( form.is_valid() ):
			username = form.cleaned_data['username']

			try:
				user = User.objects.get(username=username)

				if ( user not in task.assigned.all() ):
					task.assigned.add( user )
					task.save()
					messages.info( request, "Assigned " + user.username + " to task.")
			except:
				
				messages.error( request, "User " + username + " is not a valid user.")


	return HttpResponseRedirect( '/projects/task/view/'+str(task_id)+"/" )

@login_required
def remove_task_member( request, task_id, user_id ):
	"""
	Removes a task member (assignee)

	Arguments:
		task_id - integer task ID
		user_id - integer user ID

	Returns:
		redirect back to the project view page 
	"""
	task = ProjectTask.objects.get(id=task_id)
	user = User.objects.get( id=user_id )

	if ( task.creator == request.user ):
		task.assigned.remove( user )
		task.save()

		messages.info( request, "Unassigned " + user.username)


	return HttpResponseRedirect( '/projects/task/view/'+str(task_id)+"/" )

@login_required
def edit_task( request, task_id ):
	"""
	Provides a form populated with a task's data that 
	allows the task to be updated and saved.
	"""
	task = ProjectTask.objects.get(id=task_id)

	if ( request.method == "POST"):
		form = EditTaskForm( request.POST, instance=task )
		if form.is_valid()  and request.user == task.creator:

			task.save()

			return HttpResponseRedirect( '/projects/task/view/' + str(task.id) +"/" )

		elif request.user != task.creator:
			messages.error( request, "You do not have permission to edit this task.")
			return HttpResponseRedirect( '/projects/task/view/' + str(task.id) +"/" )

		else:

			messages.error( request, "Please fill out both fields.")
			pageData = {}
			pageData['form'] = EditTaskForm( request.POST )
			pageData['task'] = ProjectTask.objects.get( id=task_id )
			return render_to_response( 'task_edit.html', RequestContext(request, pageData) )

	else:

		form = EditTaskForm(instance=task)

		args = {}
		args['form'] = form
		args['task'] = task

		return render_to_response('task_edit.html', RequestContext(request, args) )

@login_required
def view_all_task( request, proj_id ):
	"""
	Lists all of the tasks for a selected project 
	"""
	project = Project.objects.get(id=proj_id)

	if request.user in project.members.all():
		args = {}
		args['tasks'] = ProjectTask.objects.filter( Q(openOn=project)|Q(closedOn=project)) 
		args['project'] = project
		return HttpResponseRedirect( '/projects/view/'+str(proj_id)+'/#tasks')
		#return render_to_response('task_list.html', args)

	else:
		return HttpResponseRedirect('/projects/')

@login_required
def view_all_work( request, proj_id ):
	"""
	Lists all of the work logged on a selected 
	project
	"""
	project = Project.objects.get(id=proj_id)

	if request.user in project.members.all():
		args = {}
		args['project'] = project
		args['logs'] = Worklog.objects.filter(project=project)
		return HttpResponseRedirect( '/projects/view/' + str(proj_id) + "/#worklogs")
		#return render_to_response('worklog_list.html', args)

	else:
		return HttpResponseRedirect('/projects/')

@login_required
def my_todo( request ):
	"""
	Displays the My Todo page with the list of active 
	tasks the user has assigned to them.
	"""
	tasks = apply_task_filter( request, 
		ProjectTask.objects.annotate(c=Count('openOn')).filter(c__gt=0).filter( assigned=request.user) )
	set_filter_message( request )

	args = {}
	args['user'] = request.user
	args['tasks'] = tasks.filter( inProgress=False ).all()
	args['other_num'] = len( args['tasks'] )
	args['task_wip'] = tasks.filter( inProgress=True ).all()
	args['wip_num'] = len( args['task_wip'] )
	args['num_tasks'] = len(tasks)

	return render_to_response( 'user_todo.html', RequestContext(request, args) )

@login_required
def view_tree( request, project_id=False ):
	"""
	Displays an outline view of all the user's 
	projects and tasks.
	"""
	tasks = ProjectTask.objects.annotate(c=Count('openOn')).filter(c__gt=0).filter( assigned=request.user)
	num_projects = 0
	pageData = {}


	if not project_id:
		projects = Project.objects.filter( Q(members=request.user) ).annotate(c=Count('parents')).filter( c=0 )
		pageData['treeHtml'] = ""

		for project in projects.all():
			num_projects += 1
			pageData['treeHtml'] += createTreeRow(project, tasks, depth=0 ) + createTree( project, tasks )
	else:
		projects = Project.objects.get( id=project_id )
		num_projects = 1

		pageData['treeHtml'] = createTreeRow(projects, tasks, depth=0 ) + createTree( projects, tasks )

	pageData['projects'] = projects
	pageData['tree'] = tasks
	pageData['num_projects'] = num_projects

	return render_to_response( 'project_tree.html', RequestContext( request, pageData ) )

def createTree( project, tasks, depth=0, maxdepth=15 ):

	if ( depth < maxdepth ):

		treeHtml = ""

		for p in project.subprojects.all():
			treeHtml += createTreeRow( p, tasks, depth+1 ) + createTree( p, tasks, depth=depth+1, maxdepth=maxdepth )

		return treeHtml

	else:
		return '<tr><td>Reached maximum display depth.</td></tr>'


def createTreeRow( project, tasks, depth=0 ):

	spacing = '&nbsp;&nbsp;&nbsp;' * (depth*2)
	projectRow = '<tr>\
		<td>'+spacing+'<a href="/projects/view/'+str(project.id)+'"><img src="/static/img/project.png" width="24px" />'+project.name+'</a> \
		<a title="Show Tree" href="/projects/tree/'+str(project.id)+'"><img src="/static/img/tree.jpg" width="24px" alt="Show Tree"/></a></td></tr>\n'
	applicableTasks = tasks.filter( openOn=project ).all()

	for t in applicableTasks:
		projectRow += '<tr>\
			<td>'+('&nbsp;&nbsp;&nbsp;' * (depth+1)*2 )+'<a href="/projects/task/view/'+str(t.id)+'"><img src="/static/img/task.png" width="24px" />'+t.summary+'</a>\
			</td>\
		</tr>\n'

	return projectRow

@login_required
def project_to_top( request, project_id ):
	"""
	Converts a project to a top-level project 
	in the tree by removing all of its parents 
	and removing it as a subproject from any 
	parent projects.

	Arguments:
		project_id - integer a project id 

	Returns:
		an HttpResponseRedirect to the project view 

	"""

	project = Project.objects.get( id=project_id )
	if ( request.user == project.manager ):
		for p in project.parents.all():
			project.parents.remove( p )
			p.subprojects.remove( project )
			p.save()

		project.save()
		messages.info(request, 'Project is now a top level project.')

	return HttpResponseRedirect( '/projects/view/'+str(project_id) )

@login_required
def toggle_project( request, project_id ):
	"""
	Toggles a project between being active 
	and inactive.

	Arguments:
		project_id - int a project id

	Returns:
		HttpRedirect to the referring page or project view
	"""
	project = Project.objects.get( id=project_id )

	if ( request.user == project.manager ):
		project.active = not project.active
		project.save()
		messages.info( request, "Project updated.")

	try:
		return HttpResponseRedirect(request.META['HTTP_REFERER'])
	except:
		return HttpResponseRedirect('/projects/view/'+str(project_id) )


@login_required
def convert_task_to_subproject( request, task_id ):
	"""
	Converts a task into a project and removes the 
	original task.

	Arguments:
		task_id: integer ID of the task to convert

	"""

	task = ProjectTask.objects.get( id=task_id )

	returnLocation = HttpResponseRedirect('/projects/task/view/'+str(task_id)+"/")

	if ( request.user == task.creator ):
		project = Project()
		project.manager = task.creator
		project.name = task.summary
		project.description = task.description
		project.lines = 0
		project.phase = "None"
		project.status = "None"

		project.save()
		project.members = task.assigned.all()
		project.parents = task.openOn.all()
		project.tags = task.tags.all()
		project.save()
		task.delete()

		for p in project.parents.all():
			p.subprojects.add( project )




		messages.info(request, "Task converted to project successfully. You may now edit the project attributes.")
		returnLocation = HttpResponseRedirect( '/projects/edit/'+str(project.id)+"/" )

	else:
		messages.warning( request, "You must be the creator of a task to convert it to a project." )

	return returnLocation

@login_required
def show_children( request, project_id ):
	project = Project.objects.get( id=project_id )

	pageData = {}

	pageData['projects'] = project.subprojects.all()
	pageData['project'] = project
	pageData['relation'] = "children"
	pageData['user'] = request.user

	return render_to_response( 'project_parent-sub.html', RequestContext(request, pageData) )

@login_required
def show_parents( request, project_id ):
	project = Project.objects.get( id=project_id )

	pageData = {}

	pageData['projects'] = project.parents.all()
	pageData['parents'] = pageData['projects'].count()
	pageData['project'] = project
	pageData['relation'] = "parents"
	pageData['user'] = request.user


	return render_to_response( 'project_parent-sub.html', RequestContext(request, pageData) )

@login_required
def show_outline( request ):

	pageData = {}


	try:
		projects = request.GET['pos'].split(',')
		if ( len(projects) < 1 or projects[0] == '' ):
			int('foo')

		pageData['pos'] = request.GET['pos']
	except:
		pageData['panel1'] = Project.objects.filter( members=request.user )
		pageData['empty'] = ( pageData['panel1'].count() < 1)

		return render_to_response( 'project_outline.html', RequestContext(request, pageData) )

	allProjectsInView = deepcopy(projects)

	if ( len(projects) < 3):
		projects = projects[-2:]
		pageData['panel1'] = Project.objects.filter( members=request.user )
		pageData['selected1'] = Project.objects.get( id=projects[0] )
		pageData['notfirst'] = False

	else:
		pageData['panel1pos'] = ",".join(allProjectsInView[:-2])
		previous = projects[-3]
		projects = projects[-2:]
		pageData['notfirst'] = True

		prevProject = Project.objects.get(id=previous)
		pageData['selected0'] = prevProject

		pageData['selected1'] = Project.objects.get( id=projects[0] )
		pageData['panel1'] = Project.objects.filter( parents=prevProject )
		pageData['panel1task'] = ProjectTask.objects.filter( openOn=prevProject )

	if ( len(projects) >= 1):
		if ( len(projects) == 1):
			pageData['panel2pos'] = ",".join(allProjectsInView)
		else:
			pageData['panel2pos'] = ",".join(allProjectsInView[0:-1])

		pageData['panel2'] = Project.objects.filter( parents=pageData['selected1'] )

		pageData['panel2task'] = ProjectTask.objects.filter( openOn=pageData['selected1'] )

	if ( len(projects) >= 2):
		pageData['panel3pos'] = ",".join(allProjectsInView[0:len(allProjectsInView)])


		pageData['selected2'] = Project.objects.get( id=projects[1] )
		pageData['panel3'] = Project.objects.filter( parents=pageData['selected2'])

		pageData['panel3task'] = ProjectTask.objects.filter( openOn=pageData['selected2'] )

	return render_to_response( 'project_outline.html', RequestContext(request, pageData) )

@login_required
def show_browser( request, open_project=False ):

	pageData = {}
	pageData['user'] = request.user

	if ( not open_project ):

		pageData['projects'] = Project.objects.filter( members=request.user )

	else:
		selected = Project.objects.get( id=open_project )
		pageData['selected'] = selected
		pageData['projects'] = Project.objects.filter( parents=selected )
		pageData['tasks'] = ProjectTask.objects.filter( Q(openOn=selected)|Q(closedOn=selected) ).filter( assigned=request.user )
		pageData['work'] = Worklog.objects.filter( project=selected )

	return render_to_response( 'project_browser.html', RequestContext(request, pageData) )

