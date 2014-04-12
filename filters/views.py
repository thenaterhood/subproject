from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.db.models import Q
from django.template import RequestContext

from project.models import Project
from tagging.models import Tag
from tasks.models import ProjectTask

def apply_project_filter(request, projects):
    if ('filter' in request.session):
        tags = request.session['filter']['projecttags']
        keywords = request.session['filter']['keywords']

    else:
        request.session['filter'] = {}
        request.session['filter']['projecttags'] = []
        request.session['filter']['keywords'] = []

        tags = []

    tags = Tag.objects.filter(id__in=tags)

    for t in tags:
        projects = projects.filter(tags=t)

    return projects


def apply_task_filter(request, tasks):

    if ('filter' in request.session):
        tags = request.session['filter']['tasktags']
        projects = request.session['filter']['taskprojects']
        keywords = request.session['filter']['keywords']

    else:
        reset_filter(request)
        tags = []
        projects = []

    tags = Tag.objects.filter(id__in=tags)
    projects = Project.objects.filter(id__in=projects)

    for t in tags:
        tasks = tasks.filter(tags=t)

    for p in projects:
        tasks = tasks.filter(project=p)

    return tasks


def add_task_filter(request, tag_id=False):

    if ('filter' in request.session):
        tag = Tag.objects.get(id=tag_id)
        request.session['filter_update'] = "yes"
        request.session['filter']['tasktags'].append(tag_id)

    else:
        reset_filter(request)
        request.session['filter_update'] = "yes"
        request.session['filter']['tasktags'].append(tag_id)

    return HttpResponseRedirect(request.META['HTTP_REFERER'])


def add_task_project_filter(request, project_id):
    if ('filter' in request.session):
        project = Project.objects.get(id=project_id)
        request.session['filter_update'] = "yes"
        request.session['filter']['taskprojects'].append(project_id)

    else:
        reset_filter(request)
        request.session['filter_update'] = "yes"
        request.session['filter']['projecttags'].append(tag_id)
        request.session['filter']['tasktags'].append(tag_id)

    return HttpResponseRedirect(request.META['HTTP_REFERER'])


def rm_task_project_filter(request, project_id):

    if ('filter' in request.session):
        request.session['filter_update'] = "yes"
        request.session['filter']['taskprojects'].remove(project_id)

    else:
        reset_filter(request)

    return HttpResponseRedirect(request.META['HTTP_REFERER'])


def add_filter(request, tag_id):
    if ('filter' in request.session):
        tag = Tag.objects.get(id=tag_id)
        request.session['filter_update'] = "yes"
        request.session['filter']['projecttags'].append(tag_id)
        request.session['filter']['tasktags'].append(tag_id)

    else:
        reset_filter(request)
        request.session['filter_update'] = "yes"
        request.session['filter']['projecttags'].append(tag_id)
        request.session['filter']['tasktags'].append(tag_id)

    return HttpResponseRedirect(request.META['HTTP_REFERER'])


def select_project_filter(request, tag_id=False):
    if (not tag_id):
        request.session['returnUrl'] = request.META['HTTP_REFERER']
        tags = Tag.objects.filter(Q(owner=request.user) | Q(
            users=request.user) | Q(viewers=request.user)).filter(visible=True)
        pageData = {'tags': tags}
        return render_to_response('filter_select.html', RequestContext(request, pageData))

    else:
        return add_project_filter(request, tag_id)


def select_task_filter(request, tag_id=False):
    if (not tag_id):
        request.session['returnUrl'] = request.META['HTTP_REFERER']
        tags = Tag.objects.filter(
            Q(owner=request.user) | Q(users=request.user) | Q(viewers=request.user))
        pageData = {'tags': tags}
        return render_to_response('filter_select.html', RequestContext(request, pageData))

    else:
        return add_task_filter(request, tag_id)


def add_project_filter(request, tag_id=False):
    if ('filter' in request.session):
        tag = Tag.objects.get(id=tag_id)
        request.session['filter_update'] = "yes"
        request.session['filter']['projecttags'].append(tag_id)

    else:
        reset_filter(request)
        request.session['filter_update'] = "yes"
        request.session['filter']['projecttags'].append(tag_id)

    return HttpResponseRedirect(request.META['HTTP_REFERER'])


def remove_project_filter(request, tag_id):
    if ('filter' not in request.session):
        reset_filter(request)
    else:
        if (tag_id in request.session['filter']['projecttags']):
            request.session['filter']['projecttags'].remove(tag_id)
            request.session['filter_update'] = "yes"

    return HttpResponseRedirect(request.META['HTTP_REFERER'])


def remove_task_filter(request, tag_id):
    if ('filter' not in request.session):
        reset_filter(request)
    else:
        if (tag_id in request.session['filter']['tasktags']):
            request.session['filter']['tasktags'].remove(tag_id)
            request.session['filter_update'] = "yes"

    return HttpResponseRedirect(request.META['HTTP_REFERER'])


def reset_filter(request):

    request.session['filter'] = {}
    request.session['filter']['projecttags'] = []
    request.session['filter']['tasktags'] = []
    request.session['filter']['taskprojects'] = []

    request.session['filter']['keywords'] = []
    request.session['filter_update'] = "yes"

    try:

        return HttpResponseRedirect(request.META['HTTP_REFERER'])
    except:
        return HttpResponseRedirect('/projects')


def get_project_filters(request):
    try:
        return Tag.objects.filter(id__in=request.session['filter']['projecttags'])
    except:
        reset_filter(request)
        return []


def get_task_filters(request):
    filters = []
    try:
        filters += Tag.objects.filter(
            id__in=request.session['filter']['tasktags'])
        filters += Project.objects.filter(
            id__in=request.session['filter']['taskprojects'])
        return filters
    except:
        reset_filter(request)
        return []


def set_filter_message(request):
    try:
        if ('filter' in request.session
                    and (len(request.session['filter']['projecttags']) > 0
                         or len(request.session['filter']['tasktags']) > 0
                         or len(request.session['filter']['taskprojects']) > 0)
                ):

            messages.info(
                request, "You have filters applied to this view. <a href='/projects/resetfilter/'>Reset</a>", extra_tags='safe')
    except:
        noreturn = reset_filter(request)
