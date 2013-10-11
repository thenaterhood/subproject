from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.contrib import auth
from django.core.context_processors import csrf
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from project.models import *
from project.forms import *
import project.thenaterhood.histogram as histogram

@login_required
def list_projects(request):
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
		form = CreateProjectForm(request.POST)
		if form.is_valid():
			newProj.name = form.cleaned_data['name']
			newProj.phase = form.cleaned_data['phase']
			newProj.status = form.cleaned_data['status']
			newProj.description = form.cleaned_data['description']

			newProj.manager = request.user

			newProj.save()
			newProj.members.add( request.user )

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
	worklogs = Worklog.objects.filter(project=project).all()

	args = {}
	args['project'] = project
	args['members'] = project.members.all()
	args['canEdit'] = ( project.manager == request.user )
	args['isMember'] = ( request.user in project.members.all() )
	args['worklogs'] = worklogs
	args.update(csrf(request))

	if ( project.manager == request.user ):
		args['add_member_form'] = AddMemberForm()

	return render_to_response('project_view.html', args)

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
			except:
				pass


	return HttpResponseRedirect( '/projects/view/'+str(proj_id)+"/" )

@login_required
def remove_member( request, proj_id, user_id ):
	project = Project.objects.get(id=proj_id)
	user = User.objects.get( id=user_id )

	if ( project.manager == request.user ):
		if ( user != project.manager ):
			project.members.remove( user )
			project.save()

	return HttpResponseRedirect( '/projects/view/'+str(proj_id)+"/" )

@login_required
def add_worklog( request, proj_id ):
	project = Project.objects.get(id=proj_id)

	if request.method == "POST" and request.user in project.members.all() :
		workLog = Worklog()
		form = AddWorklogForm(request.POST)
		if form.is_valid():
			workLog.hours = form.cleaned_data['hours']
			workLog.minutes = form.cleaned_data['minutes']
			workLog.summary = form.cleaned_data['summary']
			workLog.description = form.cleaned_data['description']

			workLog.owner = request.user
			workLog.project = project

			workLog.save()

			return HttpResponseRedirect('/projects/view/'+str(proj_id)+"/")

	else:

		args = {}
		args.update(csrf(request))
		args['project'] = project
		args['form'] = AddWorklogForm()

		if request.user in project.members.all():

			return render_to_response('worklog_create.html', args)

		else:

			return HttpResponseRedirect('/projects/')

@login_required
def view_worklog( request, log_id ):
	worklog = Worklog.objects.get(id=log_id)

	args = {}
	args['worklog'] = worklog
	args['canEdit'] = ( request.user == worklog.owner )
	args['project'] = worklog.project

	return render_to_response('worklog_view.html', args)

@login_required
def edit_worklog( request, log_id ):
	worklog = Worklog.objects.get(id=log_id)
	if ( request.method == "POST" and worklog.owner == request.user ):
		form = UpdateWorklogForm( request.POST )
		if form.is_valid():
			worklog.summary = form.cleaned_data['summary']
			worklog.description = form.cleaned_data['description']
			worklog.hours = form.cleaned_data['hours']
			worklog.minutes = form.cleaned_data['minutes']

			worklog.save()

			return HttpResponseRedirect( '/projects/work/view/' + str(worklog.id) +"/" )

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











