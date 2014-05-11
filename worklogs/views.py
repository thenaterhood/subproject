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
from django.db.models import Sum

from copy import deepcopy

import dateutil.parser

from worklogs.forms import EditWorklogForm
from worklogs.forms import EditSettingsForm

from worklogs.models import Worklog
from worklogs.models import WorklogPrefs

from project.models import Project
from project.models import TimelineEvent

from project.forms import UploadFileForm

import csv


@login_required
def import_worklog_csv(request):
    pageData = {}

    if (request.method == 'POST'):
        form = UploadFileForm(request.POST, request.FILES)

        if form.is_valid() and (request.FILES['file'].size / (1024 * 1024)) < 2:
            reader = csv.DictReader(
                request.FILES['file'].read().decode().splitlines())
            imported = 0
            failed = 0
            for row in reader:
                if ('name' in row):

                    matchingProjects = Project.objects.filter(
                        Q(manager=request.user) | Q(members=request.user)).filter(name=row['name']).count()

                    if (matchingProjects > 0):
                        project = Project.objects.filter(
                            Q(manager=request.user) | Q(members=request.user)).filter(name=row['name'])[0]

                        if ('duration' in row and row['duration'] != None):
                            try:
                                row['hours'] = float(
                                    row['duration'].split('.')[0])
                            except:
                                row['hours'] = 0

                            try:
                                if ('.' in row['duration']):
                                    row['minutes'] = float(
                                        "." + row['duration'].split('.'[1])) * 60
                                else:
                                    row['minutes'] = 0
                            except:
                                row['minutes'] = 0

                        if ('datestamp' in row and row['datestamp'] != None):
                            try:
                                row['datestamp'] = dateutil.parser.parse(
                                    row['datestamp'])
                            except:
                                pass

                        if ('description' in row and row['description'] != None):
                            row['summary'] = " ".join(
                                row['description'].split()[0:3])

                        addWorklog = EditWorklogForm(row)
                        if (addWorklog.is_valid()):
                            log = addWorklog.save(
                                owner=request.user, project=project)
                            if('datestamp' in row):
                                log.datestamp = row['datestamp']
                                log.save()

                            imported += 1

            messages.info(request, "Successfully imported " + str(imported) +
                          " worklogs. " + str(failed) + " could not be imported.")

        else:
            messages.error(
                request, "Unable to import worklogs from your file.")

        return HttpResponseRedirect('/projects/')

    else:
        pageData['form'] = UploadFileForm()
        pageData['sendback'] = "/projects/importcsv/work/"
        messages.info( request, "Import worklogs from a CSV file. The file should be well-formed \
			and should contain at least two columns: the project name in the 'name' column \
			and the work description in the 'description' column.")

        return render_to_response('upload_csv.html', RequestContext(request, pageData))


@login_required
def add_worklog(request, proj_id):
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

            workLog = form.save(owner=request.user, project=project)

            event = TimelineEvent()
            event.member = request.user
            event.title = "added a new worklog to " + project.name
            event.description = workLog.description
            event.category = "work"
            event.related_key = workLog.id
            event.save()

            event.viewers = project.members.all()

            messages.info(request, "Worklog saved successfully.")

            return HttpResponseRedirect('/projects/work/view/' + str(workLog.id) + "/")

        else:

            messages.error(request, "Form information is incorrect.")
            args['form'] = EditWorklogForm(request.POST)

            return render_to_response('worklog_create.html', RequestContext(request, args))

    else:

        if request.user in project.members.all():
            return render_to_response('worklog_create.html', RequestContext(request, args))

        else:

            return HttpResponseRedirect('/projects/')


@login_required
def view_worklog(request, log_id):
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
    args['canEdit'] = (request.user == worklog.owner)
    args['project'] = worklog.project

    return render_to_response('worklog_view.html', RequestContext(request, args))

@login_required
def edit_settings(request):
  settings = _get_worklog_prefs(request.user)

  if ( request.method == 'POST' ):
    postData = deepcopy(request.POST)

    if ('public' not in request.POST):
        postData['public'] = 'off'

    form = EditSettingsForm( postData, instance=settings )
    if ( form.is_valid() ):
      wprefs = form.save()
      wprefs.public = (postData['public'] != 'off')
      wprefs.save()

      form = EditSettingsForm(instance=wprefs)


      messages.info(request, "Your worklog settings have been updated." )
    else:
      messages.error(request, "There was an error saving your worklog settings.")
  else:
    form = EditSettingsForm(instance=settings)

  pageData = {}
  pageData['form'] = form
  pageData['user'] = request.user
  return render_to_response('worklog_settings.html', RequestContext(request, pageData) )


def _get_worklog_prefs(user):
    wpref = False
    try:
      wpref = WorklogPrefs.objects.get(owner=user)
    except:
      wpref = WorklogPrefs()
      wpref.owner = user
      wpref.save()

    return wpref

def list_worklogs(request, user=False):
    """
    Lists the user's worklogs
    """
    pageData = {}

    if ( user == False and request.user.is_authenticated() ):
      pageData['logs'] = Worklog.objects.filter(owner=request.user).order_by("-datestamp")
      pageData['owner'] = request.user

    else:
      creator = User.objects.get(username__iexact=user)

      if ( creator == request.user ):
        pageData['logs'] = Worklog.objects.filter(owner=creator).order_by("-datestamp")
        pageData['owner'] = creator
      else:
        pref = _get_worklog_prefs( creator )
        if ( pref.public ):
          pageData['logs'] = Worklog.objects.filter(owner=creator).order_by("-datestamp")
          pageData['owner'] = creator
        else:
          pageData['owner'] = creator
          pageData['logs'] = []

    return render_to_response('worklog_list.html', pageData)


@login_required
def edit_worklog(request, log_id=False, proj_id=False):
    """
    Displays a worklog's data and allows for it
    to be edited and saved.
    """
    worklog = Worklog.objects.get(id=log_id)

    if (request.method == "POST" and worklog.owner == request.user):
        form = EditWorklogForm(request.POST, instance=worklog)
        if form.is_valid():

            oldTime = worklog.minutes + (worklog.hours * 60)

            worklog = form.save()

            newTime = worklog.minutes + (worklog.hours * 60)

            logTimeChange = newTime - oldTime

            messages.info(request, "Worklog updated.")

            return HttpResponseRedirect('/projects/work/view/' + str(worklog.id) + "/")

        else:
            messages.error(request, "Invalid form information.")
            pageData = {}
            pageData['form'] = EditWorklogForm(request.POST)

            return render_to_response('worklog_edit.html', RequestContext(request, pageData))

    else:

        form = EditWorklogForm(instance=worklog)

        args = {}
        args['form'] = form
        args['worklog'] = worklog

        return render_to_response('worklog_edit.html', RequestContext(request, args))
