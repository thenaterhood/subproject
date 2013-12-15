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

from project.models import *
from project.forms import *
import project.thenaterhood.histogram as histogram

def ensure_userstat_exists( user ):

	try:
		UserStatistic.objects.get(user=user)
	except:
		
		userStat = UserStatistic()
		userStat.user = user

		userStat.save()


@login_required
def project_welcome(request):

	ensure_userstat_exists( request.user )

	# Assemble a collection of statistics to render to the template
	args = {}
	userStats = UserStatistic.objects.get( user=request.user )
	args['total_projects'] = len( Project.objects.filter(members=request.user) )
	args['managed_projects'] = len( Project.objects.filter(manager=request.user) )
	args['total_worklogs'] = userStats.worklogs
	tasks = Worklog.objects.filter(owner=request.user).reverse()
	args['total_time'] = str( userStats.loggedTime / 60 )
	args['start_date'] = userStats.startDate
	args['end_date'] = userStats.endDate
	args['tasks'] = tasks[:5]
	args['numTasks'] = len(	ProjectTask.objects.filter( assigned=request.user ).annotate(c=Count('openOn')).filter(c__gt=0).all())

	args['avg_task_time'] = 0
	if ( userStats.worklogs > 0 ):
		args['avg_task_time'] = str( (userStats.loggedTime/60) / userStats.worklogs )

	return render_to_response('project_welcome.html', args)

@login_required
def user_all_tasks(request):

	tasks = ProjectTask.objects.filter( creator=request.user )

	args = {}
	args['user'] = request.user
	args['tasks'] = tasks
	args['num_tasks'] = len(tasks)
	args['notodo'] = True

	return render_to_response( 'user_todo.html', args)


@login_required
def list_projects(request):
	ensure_userstat_exists( request.user )

	projects = Project.objects.filter(members=request.user)
	managedProjects = Project.objects.filter(manager=request.user)

	args = {}
	args['projects'] = projects
	args['owned'] = managedProjects
	args['num_projects'] = len(projects)

	return render_to_response('project_list.html', args)

@login_required
def create_project(request):

	if request.method == "POST":
		newProj = Project()
		newStat = ProjectStatistic()
		form = CreateProjectForm(request.POST)
		if form.is_valid():
			newProj.name = form.cleaned_data['name']
			newProj.phase = form.cleaned_data['phase']
			newProj.status = form.cleaned_data['status']
			newProj.description = form.cleaned_data['description']

			newProj.manager = request.user

			newProj.save()
			newProj.members.add( request.user )
			newStat.project = newProj

			newStat.save()

			newProj.save()

			return HttpResponseRedirect('/projects/')

	else:

		args = {}
		args.update(csrf(request))
		args['form'] = CreateProjectForm()

		return render_to_response('project_create.html', args)

@login_required
def edit_project(request, proj_id):
	project = Project.objects.get(id=proj_id)
	if ( request.method == "POST" and project.manager == request.user ):
		form = UpdateProjectForm( request.POST )
		if form.is_valid():
			project.name = form.cleaned_data['name']
			project.status = form.cleaned_data['status']
			project.phase = form.cleaned_data['phase']
			project.lines = form.cleaned_data['lines']
			project.description = form.cleaned_data['description']

			project.save()

			return HttpResponseRedirect( '/projects/view/' + str(project.id) +"/" )

	else:
		initialDict = { 
		"name": project.name, 
		"status": project.status, 
		"phase": project.phase, 
		"description": project.description,
		"lines": project.lines
		}

		form = UpdateProjectForm()
		form.initial = initialDict

		args = {}
		args['form'] = form
		args.update(csrf(request))
		args['project'] = project

		return render_to_response('project_edit.html', args)


@login_required
def view_project(request, proj_id):
	project = Project.objects.get(id=proj_id)
	worklogs = Worklog.objects.filter(project=project).all().reverse()[:5]

	args = {}
	args['project'] = project
	args['members'] = project.members.all()
	args['canEdit'] = ( project.manager == request.user )
	args['isMember'] = ( request.user in project.members.all() )
	args['worklogs'] = worklogs
	args['tasks'] = ProjectTask.objects.filter( Q(openOn=project)|Q(closedOn=project) ).reverse()[:5]
	args.update(csrf(request))

	if ( project.manager == request.user ):
		args['add_member_form'] = AddMemberForm()

	return render_to_response('project_view.html', RequestContext(request, args) )

@login_required
def add_member(request, proj_id):
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
	project = Project.objects.get(id=proj_id)
	args = {}
	args.update(csrf(request))
	args['project'] = project
	form = AddWorklogForm()
	args['form'] = form

	if (request.method == "POST") and (request.user in project.members.all() or request.user == project.manager):
		workLog = Worklog()

		form = AddWorklogForm(request.POST)

		if form.is_valid():

			try:
				workLog.hours = form.cleaned_data['hours']
				workLog.minutes = form.cleaned_data['minutes']
			except:
				workLog.hours = 0
				workLog.minutes = 0

			workLog.summary = form.cleaned_data['summary']
			workLog.description = form.cleaned_data['description']

			workLog.owner = request.user
			workLog.project = project

			# Update the ProjectStatistic assoc with the project
			ProjectStatistic.objects.filter(project=project).update(worklogs=F("worklogs") + 1)
			ProjectStatistic.objects.filter(project=project).update(loggedTime=F("loggedTime") + (workLog.minutes + (workLog.hours * 60) ) )

			UserStatistic.objects.filter(user=request.user).update(worklogs=F("worklogs") + 1 )
			UserStatistic.objects.filter(user=request.user).update(loggedTime=F("loggedTime") + (workLog.minutes + (workLog.hours * 60) ) )


			workLog.save()

			messages.info( request, "Worklog saved successfully.")

			return HttpResponseRedirect('/projects/work/view/'+str(workLog.id)+"/")

		else:

			messages.error( request, "Form information is incorrect." )
			args['form'] = form

			return HttpResponseRedirect( '/projects/addwork/'+str(project.id) )

	else:


		if request.user in project.members.all():

			return render_to_response('worklog_create.html', RequestContext(request, args) )

		else:

			return HttpResponseRedirect('/projects/')

@login_required
def view_worklog( request, log_id ):
	worklog = Worklog.objects.get(id=log_id)

	args = {}
	args['worklog'] = worklog
	args['canEdit'] = ( request.user == worklog.owner )
	args['project'] = worklog.project

	return render_to_response('worklog_view.html', RequestContext(request, args) )

@login_required
def edit_worklog( request, log_id ):
	worklog = Worklog.objects.get(id=log_id)
	projStat = ProjectStatistic.objects.get( project=worklog.project )

	if ( request.method == "POST" and worklog.owner == request.user ):
		form = UpdateWorklogForm( request.POST )
		if form.is_valid():

			oldTime = worklog.minutes + (worklog.hours * 60)

			worklog.summary = form.cleaned_data['summary']
			worklog.description = form.cleaned_data['description']
			worklog.hours = form.cleaned_data['hours']
			worklog.minutes = form.cleaned_data['minutes']

			newTime = worklog.minutes + (worklog.hours * 60)

			logTimeChange = newTime - oldTime

			worklog.save()

			# Update the ProjectStatistic for the new time
			UserStatistic.objects.filter(user=worklog.owner).update(loggedTime=F("loggedTime") + logTimeChange )
			ProjectStatistic.objects.filter(project=worklog.project).update(loggedTime=F("loggedTime") + logTimeChange)

			messages.info( request, "Worklog updated.")

			return HttpResponseRedirect( '/projects/work/view/' + str(worklog.id) +"/" )

		else:
			messages.error( request, "Invalid information.")

			return HttpResponseRedirect( '/projects/work/edit/' + str(worklog.id) )

	else:
		initialDict = { 
		"summary": worklog.summary, 
		"minutes": worklog.minutes, 
		"hours": worklog.hours, 
		"description": worklog.description,
		}

		form = UpdateWorklogForm()
		form.initial = initialDict

		args = {}
		args['form'] = form
		args.update(csrf(request))
		args['worklog'] = worklog

		return render_to_response('worklog_edit.html', args)

@login_required
def line_stats(request):

	projects = Project.objects.filter(members=request.user)

	projectDict = {}

	for p in projects:
		projectDict[p.name] = p.lines

	hist = histogram.generateHistogram(projectDict)

	args = {}
	args['histogram'] = hist

	return render_to_response('project_stats_lines.html', args)






@login_required
def time_stats(request):

	pass


@login_required
def add_task( request, proj_id=False ):

	project = Project.objects.get(id=proj_id)

	if request.method == "POST" and request.user in project.members.all() :
		projTask = ProjectTask()
		form = AddTaskForm(request.POST)
		if form.is_valid():
			projTask.summary = form.cleaned_data['summary']
			projTask.description = form.cleaned_data['description']

			projTask.creator = request.user

			# Update the ProjectStatistic assoc with the project
			ProjectStatistic.objects.filter(project=project).update(issues=F("issues") + 1)

			UserStatistic.objects.filter(user=request.user).update(issues=F("issues") + 1 )


			projTask.save()
			projTask.assigned.add( request.user )
			projTask.openOn.add( project )
			projTask.save()

			messages.info( request, "Task Saved." )

			return HttpResponseRedirect('/projects/task/view/'+str(projTask.id)+"/")

		else:
			messages.error( request, "Invalid form information." )
			return HttpResponseRedirect('/projects')

	else:

		args = {}
		args.update(csrf(request))
		args['project'] = project
		args['form'] = AddTaskForm()

		if request.user in project.members.all():

			return render_to_response('task_create.html', RequestContext(request, args) )

		else:

			return HttpResponseRedirect('/projects/')

@login_required
def view_task(request, task_id):

	task = ProjectTask.objects.get(id=task_id)
	projects = task.openOn.all()

	args = {}
	args['openOn'] = task.openOn.all()
	args['closedOn'] = task.closedOn.all()
	args['task'] = task
	args['members'] = task.assigned.all()
	args['canEdit'] = ( task.creator == request.user )
	args['isMember'] = ( request.user in task.assigned.all() )

	args.update(csrf(request))

	args['add_member_form'] = AddMemberForm()

	return render_to_response('task_view.html', RequestContext(request, args) )

@login_required
def close_task_in_project( request, project_id, task_id ):
	task = ProjectTask.objects.get(id=task_id)

	project = Project.objects.get( id=project_id )

	if ( request.user in task.assigned.all() or request.user == task.creator ):
		task.openOn.remove( project )
		task.closedOn.add( project )

		task.save()

	return HttpResponseRedirect( request.META['HTTP_REFERER'] )

@login_required
def open_task_in_project( request, project_id, task_id ):

	task = ProjectTask.objects.get(id=task_id)
	project = Project.objects.get( id=project_id )

	if ( request.user in task.assigned.all() or request.user == task.creator ):
		task.openOn.add( project )
		task.closedOn.remove( project )
		task.save()

	return HttpResponseRedirect(request.META['HTTP_REFERER'])

@login_required
def add_existing_task_to_project( request, task_id, project_id=False ):

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
	task = ProjectTask.objects.get(id=task_id)
	user = User.objects.get( id=user_id )

	if ( task.creator == request.user ):
		task.assigned.remove( user )
		task.save()

		messages.info( request, "Unassigned " + user.username)


	return HttpResponseRedirect( '/projects/task/view/'+str(task_id)+"/" )

@login_required
def edit_task( request, task_id ):
	task = ProjectTask.objects.get(id=task_id)

	if ( request.method == "POST" and ( request.user in task.assigned.all() or request.user == task.creator ) ):
		form = UpdateTaskForm( request.POST )
		if form.is_valid():

			task.summary = form.cleaned_data['summary']
			task.description = form.cleaned_data['description']

			task.save()

			return HttpResponseRedirect( '/projects/task/view/' + str(task.id) +"/" )

	else:
		initialDict = { 
		"summary": task.summary, 
		"description": task.description,
		}

		form = UpdateTaskForm()
		form.initial = initialDict

		args = {}
		args['form'] = form
		args.update(csrf(request))
		args['task'] = task

		return render_to_response('task_edit.html', args)

@login_required
def view_all_task( request, proj_id ):
	project = Project.objects.get(id=proj_id)

	if request.user in project.members.all():
		args = {}
		args['tasks'] = ProjectTask.objects.filter( Q(openOn=project)|Q(closedOn=project)) 
		args['project'] = project
		return render_to_response('task_list.html', args)

	else:
		return HttpResponseRedirect('/project/')

@login_required
def view_all_work( request, proj_id ):
	project = Project.objects.get(id=proj_id)

	if request.user in project.members.all():
		args = {}
		args['project'] = project
		args['logs'] = Worklog.objects.filter(project=project)
		return render_to_response('worklog_list.html', args)

	else:
		return HttpResponseRedirect('/project/')

@login_required
def my_todo( request ):
	tasks = ProjectTask.objects.annotate(c=Count('openOn')).filter(c__gt=0)

	args = {}
	args['user'] = request.user
	args['tasks'] = tasks
	args['num_tasks'] = len(tasks)

	return render_to_response( 'user_todo.html', args)











