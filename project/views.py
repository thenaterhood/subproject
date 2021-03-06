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

import dateutil.parser
import operator

from copy import deepcopy

from project.models import *
from project.forms import *
from filters.views import *

from tasks.models import ProjectTask

from tagging.models import Tag

from worklogs.models import Worklog

from user.forms import AddMemberForm

import csv
import string


@login_required
def show_import_page(request):
    return render_to_response('project_import.html', RequestContext(request, {}))


@login_required
def import_project_csv(request):
    pageData = {}
    if (request.method == 'POST'):
        form = UploadFileForm(request.POST, request.FILES)

        if form.is_valid() and (request.FILES['file'].size / (1024 * 1024)) < 2:

            reader = csv.DictReader(
                request.FILES['file'].read().decode().splitlines())

            imported = 0

            for row in reader:

                if ('status' not in row or row['status'] == None):
                    row['status'] = "None"

                if ('phase' not in row or row['phase'] == None):
                    row['phase'] = "None"

                if ('description' not in row or row['description'] == None):
                    row['description'] = "[Imported Project]"
                else:
                    row['description'] = "[Imported Project] " + \
                        row['description']

                row['public'] = 'off'

                addForm = EditProjectForm(row)


                if( addForm.is_valid() ):

                    name = addForm.cleaned_data['name']
                    allowedChars = string.ascii_lowercase + string.ascii_uppercase + string.digits + '. -_'

                    existing = Project.objects.filter(manager=request.user).filter(name__iexact=name).count()

                    if ( existing == 0 and set(name) <= set(allowedChars) ):

                        p = addForm.save(owner=request.user)
                        p.public = False
                        p.save()

                        imported += 1


            if imported > 0:
                messages.info(
                    request, "Successfully imported " + str(imported) + " projects.")
            else:
                messages.warning(
                    request, "No projects could be imported from your file.")
        else:
            messages.error(request, "Unable to import projects.")

        return HttpResponseRedirect('/projects/')

    else:
        pageData['form'] = UploadFileForm()
        pageData['sendback'] = '/projects/importcsv/projects/'
        messages.info( request, "Import projects from a CSV file. The CSV file must be well-formed and must \
			include at least one column with the header 'name' that contains project names.")
        return render_to_response('upload_csv.html', RequestContext(request, pageData))


@login_required
def project_welcome(request):
    """
    Renders the project dashboard with
    basic user statistics.
    """

    # Assemble a collection of statistics to render to the template
    args = {}

    messages.warning( request, "This application is currently under heavy development and is not \
		hosted in an environment capable of handling 'real-world' usage. Reliability and \
		security cannot be guaranteed at this point in development. Please use this service only as \
		a preview of what's to come.")

    args['total_projects'] = Project.objects.filter(
        members=request.user).count()
    args['managed_projects'] = Project.objects.filter(
        manager=request.user).count()

    args['total_worklogs'] = Worklog.objects.filter(owner=request.user).count()

    args['total_tasks'] = ProjectTask.objects.filter(
        creator=request.user).count()
    args['active_tasks'] = ProjectTask.objects.filter(
        creator=request.user).filter(inProgress=True).count()

    total_time = (
        (Worklog.objects.filter( owner=request.user ).aggregate(Sum('minutes'))['minutes__sum'] or 0) / 60 ) + \
        (Worklog.objects.filter(owner=request.user).aggregate(
            Sum('hours'))['hours__sum'] or 0)

    args['total_time'] = "%0.2f" % total_time

    args['start_date'] = request.user.date_joined

    args['numTasks'] = ProjectTask.objects.filter(
        assigned=request.user).filter(completed=False).count()

    args['avg_task_time'] = 0

    timelineItems = TimelineEvent.objects.filter(
        Q(member=request.user) | Q(viewers=request.user)).distinct().order_by('-datestamp')

    args['timeline'] = timelineItems[0:50]

    if (args['total_worklogs'] > 0):
        args['avg_task_time'] = "%0.2f" % (
            total_time / args['total_worklogs'] )

        args['end_date'] = Worklog.objects.filter(
            owner=request.user).order_by('-datestamp')[0].datestamp
    else:
        args['end_date'] = "No recent logs."

    return render_to_response('project_welcome.html', RequestContext(request, args))

def list_projects(request, user=False):
    """
    Displays a list of all the projects a user
    is associated with.
    """
    args = {}
    args['currentUser'] = request.user

    if ( not request.user.is_authenticated() and not user ):
        return HttpResponseRedirect('/')

    if ( user == False ):
        projects = apply_project_filter(
            request, Project.objects.filter(members=request.user)).order_by("name")
        set_filter_message(request)
        managedProjects = Project.objects.filter(manager=request.user)
        args['owned'] = managedProjects
        args['title'] = "My Projects"
        args['tags'] = Tag.objects.filter(Q(owner=request.user) | Q(
            users=request.user) | Q(viewers=request.user)).order_by("name")

    else:
        args['title'] = user + "'s Projects"
        manager = User.objects.get(username__iexact=user)

        if ( request.user.is_authenticated() ):
            args['tags'] = Tag.objects.filter(Q(owner=request.user) | Q(
                users=request.user) | Q(viewers=request.user) | Q(owner=manager,public=True)).order_by("name")

            projects = apply_project_filter( request, Project.objects.filter(manager=manager).filter( Q(public=True)|Q(members=request.user) ) ).distinct().order_by("name")
        else:
            args['tags'] = Tag.objects.filter( Q(owner=manager,public=True)).order_by("name")

            projects = apply_project_filter( request, Project.objects.filter(manager=manager).filter( Q(public=True) ) ).distinct().order_by("name")


    args['projects'] = projects
    args['num_projects'] = len(projects)

    args['filters'] = get_project_filters(request)

    return render_to_response('project_list.html', RequestContext(request, args))


@login_required
def create_project(request, parent=False, pid=False):
    """
    Provides a new project form and adds
    a project to the database after verifying
    the data.
    """

    if request.method == "POST":


        postData = deepcopy(request.POST)

        if ('public' not in request.POST):
            postData['public'] = 'off'


        if ( pid != False ):
            project = Project.objects.get(id=pid)
            form = EditProjectForm(postData, instance=project)
            pActionName = "updated"
            if ( request.user != project.manager ):
                messages.warning( request, "You are not allowed to edit that project.")
                return HttpResponseRedirect('/projects/')
        else:
            project = None
            form = EditProjectForm(postData)
            pActionName = "created"

        if form.is_valid() and not "useexisting" in request.POST:

            name = form.cleaned_data['name']
            allowedChars = string.ascii_lowercase + string.ascii_uppercase + string.digits + '. -_'

            if ( pid != False ):
              existing = Project.objects.filter(manager=request.user).filter(name__iexact=name).count() -1
            else:
              existing = Project.objects.filter(manager=request.user).filter(name__iexact=name).count()

            if ( existing <= 0 and set(name) <= set(allowedChars) ):


                newProj = form.save(owner=request.user)
                newProj.public = (postData['public'] != 'off')
                newProj.save()

                event = TimelineEvent()
                event.member = request.user
                event.title = pActionName + " the project " + newProj.name
                event.description = newProj.description
                event.category = "project"
                event.related_key = newProj.id

                event.save()

                event.viewers = newProj.members.all()

                if ('parent' in request.POST and request.POST['parent'] != "False"):
                    parentProject = Project.objects.get(id=request.POST['parent'])

                    event.title = "created the subproject '" + \
                        newProj.name + "' under " + parentProject.name
                    event.viewers = parentProject.members.all()
                    newProj.parents.add(parentProject)
                    parentProject.subprojects.add(newProj)
                    parentProject.save()

                    event.save()

                newProj.save()

                if ('returnUrl' not in request.POST):
                    redirTo = '/u/'+request.user.username+"/projects/"+newProj.name
                else:
                    redirTo = request.POST['returnUrl']

                return HttpResponseRedirect(redirTo)

            else:

                pageData = {}
                pageData['form'] = EditProjectForm(request.POST)
                messages.warning(
                    request, "Sorry, you cannot use that name.")
                return render_to_response('project_create.html', RequestContext(request, pageData))


        else:

            pageData = {}
            pageData['form'] = EditProjectForm(request.POST)
            messages.warning(
                request, "Please check your input, all fields are required.")
            return render_to_response('project_create.html', RequestContext(request, pageData))

    else:

        args = {}
        args.update(csrf(request))
        try:
            args['returnUrl'] = request.META['HTTP_REFERER']
        except:
            args['returnUrl'] = '/projects/'
        args['addingSub'] = parent

        if ( pid != False ):
            project = Project.objects.get(id=pid)
            args['form'] = EditProjectForm(instance=project)
            args['pid'] = project.id
        else:
            args['form'] = EditProjectForm()
            args['pid'] = -1
        args['parent'] = parent
        return render_to_response('project_create.html', args)


def assign_child(request, parent_id, child_id=False):
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
    if (child_id):

        try:
            parent = Project.objects.get(id=parent_id)
            child = Project.objects.get(id=child_id)

            parent.subprojects.add(child)
            child.parents.add(parent)

            parent.save()
            child.save()

            if ("returnUrl" in request.session):
                returnUrl = request.session['returnUrl']
                del request.session['returnUrl']
                return HttpResponseRedirect(returnUrl)
            else:
                return HttpResponseRedirect('/projects/view/' + str(parent_id))

        except:
            return HttpResponseRedirect('/projects/')

    else:
        pageData = {}
        parentProj = Project.objects.get(id=parent_id)

        pageData['projects'] = Project.objects.filter(
            manager=request.user).exclude(id=parent_id).exclude(parents=parentProj)
        return render_to_response('project_select.html', RequestContext(request, pageData))


def view_project(request, proj_id=False, username=False, projectname=False):
    """
    Displays a project's dashboard
    """

    if ( proj_id != False ):
        project = Project.objects.get(id=proj_id)
    elif ( username != False and projectname != False ):
        try:
            manager = User.objects.get(username=username)
            project = Project.objects.get(manager=manager, name__iexact=projectname)
            if ( request.user not in project.members.all() and not project.public ):
                raise Exception()
        except:
            messages.warning(request, "The project you tried to access does not exist, or you don't have permission to see it.")
            return HttpResponseRedirect('/projects')

    else:
        return HttpResponseRedirect('/projects')

    worklogs = Worklog.objects.filter(
        project=project).all().order_by('-datestamp')
    tags = project.tags.all()

    if not project.active:
        messages.warning(
            request, "This project is closed. Work and tasks cannot be added to closed projects.")

    args = {}
    args['parents'] = project.parents.all()
    args['num_parents'] = args['parents'].count()
    args['project'] = project
    args['children'] = project.subprojects.all()
    args['num_children'] = args['children'].count()
    args['members'] = project.members.all()
    args['canEdit'] = (project.manager == request.user)
    args['isMember'] = (request.user in project.members.all())
    args['num_members'] = project.members.all().count()
    args['worklogs'] = worklogs
    args['num_worklogs'] = worklogs.count()
    args['tasks'] = ProjectTask.objects.filter(project=project).order_by('-startDate')
    args['num_tasks'] = args['tasks'].count()
    if ( request.user.is_authenticated() ):
        args['tags'] = project.tags.filter(Q(owner=request.user) | Q(
            users=request.user) | Q(viewers=request.user) | Q(public=True)).filter(visible=True)
        args['yourTags'] = args['tags'].filter(
            Q(owner=request.user) | Q(users=request.user) | Q(viewers=request.user))
    else:
        args['tags'] = project.tags.filter(Q(public=True)).filter(visible=True)

    if (project.manager == request.user):
        args['add_member_form'] = AddMemberForm()

    return render_to_response('project_view.html', RequestContext(request, args))


@login_required
def unassign_task_from_project(request, task_id, project_id):
    """
    Removes a task's association with a project.

    Arguments:
            task_id: integer task ID to remove from project
            project_id: integer project ID to remove task from

    Returns:
            a redirect back to the page the request originated on
    """
    task = ProjectTask.objects.get(id=task_id)
    project = Project.objects.get(id=project_id)

    if (request.user in project.members.all() or request.user == task.creator):
        task.project = None
        task.save()

    if ('HTTP_REFERER' in request.META):
        return HttpResponseRedirect(request.META['HTTP_REFERER'])
    else:
        return HttpResponseRedirect('/projects/view/' + str(project_id))


@login_required
def add_member(request, proj_id):
    """
    Adds a member to a project
    """

    project = Project.objects.get(id=proj_id)

    if (request.method == "POST" and project.manager == request.user):
        form = AddMemberForm(request.POST)
        if (form.is_valid()):
            username = form.cleaned_data['username']

            try:
                user = User.objects.get(username=username)

                if (user not in project.members.all()):
                    project.members.add(user)
                    project.save()
                    messages.info(
                        request, "Assigned " + user.username + " to project.")
            except:
                messages.error(
                    request, "User " + username + " is not a valid user.")

    return HttpResponseRedirect('/projects/view/' + str(proj_id) + "/")


@login_required
def remove_member(request, proj_id, user_id):
    """
    Removes a member from a project.
    """
    project = Project.objects.get(id=proj_id)
    user = User.objects.get(id=user_id)

    if (project.manager == request.user):
        if (user != project.manager):
            project.members.remove(user)
            project.save()
            messages.info(
                request, "Removed " + user.username + " from project.")

    return HttpResponseRedirect('/projects/view/' + str(proj_id) + "/")


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
def add_existing_task_to_project(request, task_id, project_id=False):
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

    if (project_id != False):
        project = Project.objects.get(id=project_id)

        if ((request.user == task.creator and request.user == project.manager)
                or (request.user in task.assigned.all() and request.user in project.members.all())):

            task.project = project
            task.save()

            return HttpResponseRedirect('/projects/task/view/' + str(task_id) + "/")

        else:
            return HttpResponseRedirect('/projects/welcome')

    else:

        args = {}
        args['task'] = task

        args['projects'] = Project.objects.filter(members=request.user)

        return render_to_response('project_select.html', args)


@login_required
def assign_task(request, proj_id, task_id=False):
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
    if (task_id):
        project = Project.objects.get(id=proj_id)
        task = ProjectTask.objects.get(id=task_id)

        task.project = project
        task.save()

        messages.success(request, "Task added to project successfully.")

        if ('returnUrl' in request.session):
            return HttpResponseRedirect(request.session['returnUrl'])
        else:
            return HttpResponseRedirect('/projects/view/' + str(proj_id))

    else:
        pageData = {}
        project = Project.objects.get(id=proj_id)
        pageData['tasks'] = ProjectTask.objects.filter(creator=request.user)

        return render_to_response('task_select.html', pageData)


@login_required
def assign_project_tag(request, proj_id, tag_id=False):
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
        tags = Tag.objects.filter(
            Q(owner=request.user) | Q(users=request.user)).filter(visible=True)
        project = Project.objects.get(id=proj_id)

        pageData = {}
        pageData['project'] = project
        pageData['tags'] = tags
        pageData['allowNew'] = True

        if ('HTTP_REFERER' in request.META):
            request.session['returnUrl'] = request.META['HTTP_REFERER']

        return render_to_response('tag_select.html', RequestContext(request, pageData))

    else:

        project = Project.objects.get(id=proj_id)
        tag = Tag.objects.get(id=tag_id)

        if (request.user in tag.users.all() or request.user == tag.owner):
            project.tags.add(tag)
            project.save()

        if ('returnUrl' in request.session):
            returnUrl = request.session['returnUrl']

        return HttpResponseRedirect(returnUrl)


@login_required
def untag_project(request, project_id, tag_id):
    tag = Tag.objects.get(id=tag_id)
    project = Project.objects.get(id=project_id)

    if (request.user in tag.users.all() or request.user == tag.owner):
        project.tags.remove(tag)
        messages.info(request, "Untagged project " + project.name)

    else:
        messages.warning(request, "You are not allowed to remove this tag.")

    return HttpResponseRedirect('/projects/view/' + str(project_id))


@login_required
def toggle_project_task_status(request, task_id):
    """
    Toggles a task open or closed on a project

    Arguments:
            project_id - integer project id
            task_id - integer task id

    Returns:
            http redirect back to referring page or
            the project view page if there isn't a referer
    """
    task = ProjectTask.objects.get(id=task_id)

    if (request.user in task.assigned.all() or request.user == task.creator):

        task.completed = not task.completed
        task.save()

        messages.info(request, "Updated task status.")

    try:
        return HttpResponseRedirect(request.META['HTTP_REFERER'])
    except:
        return HttpResponseRedirect('/projects/task/view/' + str(task_id) + '/')


@login_required
def view_all_task(request, proj_id):
    """
    Lists all of the tasks for a selected project
    """
    project = Project.objects.get(id=proj_id)

    if request.user in project.members.all():
        add_task_project_filter(request, proj_id)

        return HttpResponseRedirect('/projects/usertasks/')

    else:
        return HttpResponseRedirect('/projects/')


@login_required
def view_tree(request, project_id=False):
    """
    Displays an outline view of all the user's
    projects and tasks.
    """
    tasks = ProjectTask.objects.filter(assigned=request.user)
    num_projects = 0
    pageData = {}

    if not project_id:
        projects = Project.objects.filter(Q(members=request.user)).annotate(
            c=Count('parents')).filter(c=0)
        pageData['treeHtml'] = ""

        for project in projects.all():
            num_projects += 1
            pageData[
                'treeHtml'] += createTreeRow(project, tasks, depth=0) + createTree(project, tasks)
    else:
        projects = Project.objects.get(id=project_id)
        num_projects = 1

        pageData['treeHtml'] = createTreeRow(
            projects, tasks, depth=0) + createTree(projects, tasks)

    pageData['projects'] = projects
    pageData['tree'] = tasks
    pageData['num_projects'] = num_projects

    return render_to_response('project_tree.html', RequestContext(request, pageData))


def createTree(project, tasks, depth=0, maxdepth=15):
    """
    Creates a project tree view recursively
    """

    if (depth < maxdepth):

        treeHtml = ""

        for p in project.subprojects.all():
            treeHtml += createTreeRow(p, tasks, depth + 1) + \
                createTree(p, tasks, depth=depth + 1, maxdepth=maxdepth)

        return treeHtml

    else:
        return '<tr><td>Reached maximum display depth.</td></tr>'


def createTreeRow(project, tasks, depth=0):
    """
    Creates a row in the project tree view.
    """

    spacing = '&nbsp;&nbsp;&nbsp;' * (depth * 2)
    projectRow = '<tr>\
		<td>' + spacing + '<a href="/projects/view/' + str(project.id) + '"><img src="/static/img/project.png" width="24px" />' + project.name + '</a> \
		<a title="Show Tree" href="/projects/tree/' + str(project.id) + '"><img src="/static/img/tree.jpg" width="24px" alt="Show Tree"/></a></td></tr>\n'
    applicableTasks = tasks.filter(project=project).all()

    for t in applicableTasks:
        projectRow += '<tr>\
			<td>' + ('&nbsp;&nbsp;&nbsp;' * (depth + 1) * 2 ) + '<a href="/projects/task/view/' + str(t.id) + '"><img src="/static/img/task.png" width="24px" />' + t.summary + '</a>\
			</td>\
		</tr>\n'

    return projectRow


@login_required
def project_to_top(request, project_id):
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

    project = Project.objects.get(id=project_id)
    if (request.user == project.manager):
        for p in project.parents.all():
            project.parents.remove(p)
            p.subprojects.remove(project)
            p.save()

        project.save()
        messages.info(request, 'Project is now a top level project.')

    return HttpResponseRedirect('/projects/view/' + str(project_id))


@login_required
def toggle_project(request, project_id):
    """
    Toggles a project between being active
    and inactive.

    Arguments:
            project_id - int a project id

    Returns:
            HttpRedirect to the referring page or project view
    """
    project = Project.objects.get(id=project_id)

    if (request.user == project.manager):
        project.active = not project.active
        project.save()
        messages.info(request, "Project updated.")

    try:
        return HttpResponseRedirect(request.META['HTTP_REFERER'])
    except:
        return HttpResponseRedirect('/projects/view/' + str(project_id))


@login_required
def convert_task_to_subproject(request, task_id):
    """
    Converts a task into a project and removes the
    original task.

    Arguments:
            task_id: integer ID of the task to convert

    """

    task = ProjectTask.objects.get(id=task_id)

    returnLocation = HttpResponseRedirect(
        '/projects/task/view/' + str(task_id) + "/")

    if (request.user == task.creator):
        project = Project()
        project.manager = task.creator
        project.name = task.summary
        project.description = task.description
        project.lines = 0
        project.phase = "None"
        project.status = "None"

        project.save()
        project.members = task.assigned.all()
        project.parents = [task.project]
        project.tags = task.tags.all()
        project.save()
        task.delete()

        for p in project.parents.all():
            p.subprojects.add(project)

        messages.info(
            request, "Task converted to project successfully. You may now edit the project attributes.")
        returnLocation = HttpResponseRedirect(
            '/projects/edit/' + str(project.id) + "/")

    else:
        messages.warning(
            request, "You must be the creator of a task to convert it to a project.")

    return returnLocation


@login_required
def show_children(request, project_id):
    project = Project.objects.get(id=project_id)

    pageData = {}

    pageData['projects'] = project.subprojects.all()
    pageData['project'] = project
    pageData['relation'] = "children"
    pageData['user'] = request.user

    return render_to_response('project_parent-sub.html', RequestContext(request, pageData))


@login_required
def show_parents(request, project_id):
    project = Project.objects.get(id=project_id)

    pageData = {}

    pageData['projects'] = project.parents.all()
    pageData['parents'] = pageData['projects'].count()
    pageData['project'] = project
    pageData['relation'] = "parents"
    pageData['user'] = request.user

    return render_to_response('project_parent-sub.html', RequestContext(request, pageData))


@login_required
def show_outline(request):

    pageData = {}

    try:
        projects = request.GET['pos'].split(',')
        if (len(projects) < 1 or projects[0] == ''):
            int('foo')

        pageData['pos'] = request.GET['pos']
    except:
        pageData['panel1'] = Project.objects.filter(members=request.user)
        pageData['empty'] = (pageData['panel1'].count() < 1)

        return render_to_response('project_outline.html', RequestContext(request, pageData))

    allProjectsInView = deepcopy(projects)

    if (len(projects) < 3):
        projects = projects[-2:]
        pageData['panel1'] = Project.objects.filter(members=request.user)
        pageData['selected1'] = Project.objects.get(id=projects[0])
        pageData['notfirst'] = False

    else:
        pageData['panel1pos'] = ",".join(allProjectsInView[:-2])
        previous = projects[-3]
        projects = projects[-2:]
        pageData['notfirst'] = True

        prevProject = Project.objects.get(id=previous)
        pageData['selected0'] = prevProject

        pageData['selected1'] = Project.objects.get(id=projects[0])
        pageData['panel1'] = Project.objects.filter(parents=prevProject)
        pageData['panel1task'] = ProjectTask.objects.filter(
            project=prevProject)

    if (len(projects) >= 1):
        if (len(projects) == 1):
            pageData['panel2pos'] = ",".join(allProjectsInView)
        else:
            pageData['panel2pos'] = ",".join(allProjectsInView[0:-1])

        pageData['panel2'] = Project.objects.filter(
            parents=pageData['selected1'])

        pageData['panel2task'] = ProjectTask.objects.filter(
            project=pageData['selected1'])

    if (len(projects) >= 2):
        pageData['panel3pos'] = ",".join(
            allProjectsInView[0:len(allProjectsInView)])

        pageData['selected2'] = Project.objects.get(id=projects[1])
        pageData['panel3'] = Project.objects.filter(
            parents=pageData['selected2'])

        pageData['panel3task'] = ProjectTask.objects.filter(
            project=pageData['selected2'])

    return render_to_response('project_outline.html', RequestContext(request, pageData))


@login_required
def show_browser(request, open_project=False):

    pageData = {}
    pageData['user'] = request.user

    if (not open_project):

        pageData['projects'] = Project.objects.filter(members=request.user)

    else:
        selected = Project.objects.get(id=open_project)
        pageData['selected'] = selected
        pageData['projects'] = Project.objects.filter(parents=selected)
        pageData['tasks'] = ProjectTask.objects.filter(
            project=selected).filter(assigned=request.user)
        pageData['work'] = Worklog.objects.filter(project=selected)

    return render_to_response('project_browser.html', RequestContext(request, pageData))
