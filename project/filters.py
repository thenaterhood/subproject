from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.db.models import Q
from django.template import RequestContext

from project.models import *

def apply_project_filter( request, projects ):
	if ( 'filter' in request.session ):
		tags = request.session['filter']['projecttags']
		keywords = request.session['filter']['keywords']

	else:
		request.session['filter'] = {}
		request.session['filter']['projecttags'] = []
		request.session['filter']['keywords'] = []

		tags = []

	tags = Tag.objects.filter( id__in=tags )

	for t in tags:
		projects = projects.filter( tags=t )

	return projects


def apply_task_filter( request, tasks ):
	if ( 'filter' in request.session ):
		tags = request.session['filter']['tasktags']
		keywords = request.session['filter']['keywords']

	else:
		reset_filter( request )
	
		tags = []

	tags = Tag.objects.filter( id__in=tags )
	
	for t in tags:
		tasks = tasks.filter( tags=t )

	return tasks

def add_task_filter( request, tag_id=False ):

	if ( 'filter' in request.session ):
		tag = Tag.objects.get( id=tag_id )
		request.session['filter_update'] = "yes"
		request.session['filter']['tasktags'].append( tag_id )

	else:
		reset_filter( request )
		request.session['filter_update'] = "yes"
		request.session['filter']['tasktags'].append( tag_id )

	return HttpResponseRedirect(request.META['HTTP_REFERER'])

def add_filter( request, tag_id ):
	if ( 'filter' in request.session ):
		tag = Tag.objects.get( id=tag_id )
		request.session['filter_update'] = "yes"
		request.session['filter']['projecttags'].append( tag_id )
		request.session['filter']['tasktags'].append(tag_id)

	else:
		reset_filter( request )
		request.session['filter_update'] = "yes"
		request.session['filter']['projecttags'].append( tag_id )
		request.session['filter']['tasktags'].append(tag_id)


	return HttpResponseRedirect(request.META['HTTP_REFERER'])


def select_project_filter( request, tag_id=False ):
	if ( not tag_id ):
		request.session['returnUrl'] = request.META['HTTP_REFERER']
		tags = Tag.objects.filter( Q(owner=request.user)|Q(users=request.user)|Q(viewers=request.user) ).filter(visible=True)
		pageData = { 'tags':tags }
		return render_to_response( 'filter_select.html', RequestContext(request, pageData) )

	else:
		return add_project_filter( request, tag_id )

def select_task_filter( request, tag_id=False ):
	if ( not tag_id ):
		request.session['returnUrl'] = request.META['HTTP_REFERER']
		tags = Tag.objects.filter( Q(owner=request.user)|Q(users=request.user)|Q(viewers=request.user) )
		pageData = { 'tags':tags }
		return render_to_response( 'filter_select.html', RequestContext(request, pageData) )

	else:
		return add_task_filter( request, tag_id )



def add_project_filter( request, tag_id=False ):
	if ( 'filter' in request.session ):
		tag = Tag.objects.get( id=tag_id )
		request.session['filter_update'] = "yes"
		request.session['filter']['projecttags'].append( tag_id )

	else:
		reset_filter( request )
		request.session['filter_update'] = "yes"
		request.session['filter']['projecttags'].append( tag_id )

	return HttpResponseRedirect(request.META['HTTP_REFERER'])

def remove_project_filter( request, tag_id ):
	if ( 'filter' not in request.session ):
		reset_filter( request )
	else:
		if ( tag_id in request.session['filter']['projecttags'] ):
			request.session['filter']['projecttags'].remove( tag_id )
			request.session['filter_update'] = "yes"

	return HttpResponseRedirect(request.META['HTTP_REFERER'])

def remove_task_filter( request, tag_id ):
	if ( 'filter' not in request.session ):
		reset_filter( request )
	else:
		if ( tag_id in request.session['filter']['tasktags'] ):
			request.session['filter']['tasktags'].remove( tag_id )
			request.session['filter_update'] = "yes"


	return HttpResponseRedirect(request.META['HTTP_REFERER'])



def reset_filter( request ):

	request.session['filter'] = {}
	request.session['filter']['projecttags'] = []
	request.session['filter']['tasktags'] = []

	request.session['filter']['keywords'] = []		
	request.session['filter_update'] = "yes"

	try:

		return HttpResponseRedirect( request.META['HTTP_REFERER'] )
	except:
		return HttpResponseRedirect('/projects')


def get_project_filters( request ):
	try:
		return Tag.objects.filter( id__in=request.session['filter']['projecttags'] )
	except:
		reset_filter( request )
		return []


def get_task_filters( request ):
	try:
		return Tag.objects.filter( id__in=request.session['filter']['tasktags'] )
	except:
		reset_filter( request )
		return []

def set_filter_message( request ):
	try:
		if ( 'filter' in request.session and ( len(request.session['filter']['projecttags']) > 0 or len(request.session['filter']['tasktags']) > 0 ) ):
			projecttags = get_project_filters( request )
			tasktags = get_task_filters( request )
			tagmessage = "This view is being filtered by tags you selected. <a href='/projects/resetfilter'>Remove This Filter</a><br />"
			tagmessage += "Project Tags: "
			for t in projecttags:
				tagmessage += "\n \
				<a href='/projects/rmprojectfilter/"+str(t.id)+"/' title='Remove Filter Tag'>\
				<img src='/static/img/delete.png' width='16px' alt='X'/>\
				</a><a href='/projects/tags/" + str( t.id ) + "/'>" + t.name + "</a>&nbsp;&nbsp;&nbsp;"

			tagmessage += "<a href='/projects/filter/addprojecttag/'>(Add Another)</a>\n<br />\nTask Tags:"
			for t in tasktags:
				tagmessage += "\n \
				<a href='/projects/rmtaskfilter/"+str(t.id)+"/' title='Remove Filter Tag'>\
				<img src='/static/img/delete.png' width='16px' alt='X'/>\
				</a><a href='/projects/tags/" + str( t.id ) + "/'>" + t.name + "</a>&nbsp;&nbsp;&nbsp;"

			tagmessage += "<a href='/projects/filter/addtasktag/'>(Add Another)</a>"


			messages.info( request, tagmessage, extra_tags='safe')
	except:
		noreturn = reset_filter( request )