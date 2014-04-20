from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.core.context_processors import csrf
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import F
from django.db.models import Q
from django.contrib import messages

from tasks.models import ProjectTask
from tasks.forms import EditTaskForm

from tagging.models import Tag

from filters.views import apply_task_filter, set_filter_message, get_task_filters
from project.models import Project, TimelineEvent

from user.forms import AddMemberForm


@login_required
def tasks_by_status(request, assignee=False, status='inprogress'):
    """
    Displays the user's tasks and todo filtered 
    by the status.
    """
    inprogress = False
    completed = False
    name = 'Tasks'

    if (status == 'inprogress'):
        inprogress = True
        name = 'Tasks in Progress'

    if (status == 'complete'):
        completed = True
        name = 'Completed Tasks'

    args = {}
    args['tags'] = Tag.objects.filter(Q(owner=request.user) | Q(
        users=request.user) | Q(viewers=request.user)).order_by("name")

    if (not assignee):
        args['notodo'] = True
        tasks = apply_task_filter(request, ProjectTask.objects.filter(
            creator=request.user).order_by('-startDate'))
    else:
        tasks = apply_task_filter(
            request,
            ProjectTask.objects.filter(
                assigned=request.user).order_by('-startDate')
        )

    set_filter_message(request)

    args['user'] = request.user
    args['projects'] = Project.objects.filter(
        Q(manager=request.user) | Q(members=request.user)).distinct()
    args['tasks'] = tasks.filter(inProgress=inprogress).filter(
        completed=completed).all()
    args['other_num'] = tasks.filter(
        inProgress=inprogress).filter(completed=completed).count()
    args['other_name'] = name
    args['num_tasks'] = args['other_num']
    args['other_showmore'] = False

    args['filters'] = get_task_filters(request)

    return render_to_response('task_list.html', RequestContext(request, args))


@login_required
def all_tasks(request, user=False):

    if ( not request.user.is_authenticated() and not user ):
        return HttpResponseRedirect('/')

    args = {}

    if ( user == False and request.user.is_authenticated() ):
        args['tags'] = Tag.objects.filter(Q(owner=request.user) | Q(
            users=request.user) | Q(viewers=request.user)).order_by("name")
        args['tasks'] = apply_task_filter(request, ProjectTask.objects.filter(
            Q(creator=request.user) | Q(assigned=request.user)).distinct()).order_by('-startDate')
        args['projects'] = Project.objects.filter(
            Q(manager=request.user) | Q(members=request.user)).distinct()

    else:

        manager = User.objects.get(username__iexact=user)
        args['username'] = user
        args['usertasks'] = True

        if ( request.user.is_authenticated() ):
            args['tags'] = Tag.objects.filter(Q(owner=request.user) | Q(
                users=request.user) | Q(viewers=request.user) | Q(owner=manager,public=True)).order_by("name")
            
            args['tasks'] = apply_task_filter(request, ProjectTask.objects.filter(
                Q(creator=manager) ).filter( Q(assigned=request.user ) ).distinct() ).order_by('-startDate')

            args['projects'] = Project.objects.filter(manager=manager).filter( Q(public=True)|Q(members=request.user) ).distinct().order_by("name")

        else:
            args['tags'] = Tag.objects.filter( Q(owner=manager,public=True)).order_by("name")

            args['tasks'] = []

            args['projects'] = Project.objects.filter(manager=manager).filter( Q(public=True) ).distinct().order_by("name")





    args['other_name'] = 'All Tasks'
    args['showmore'] = False
    args['other_num'] = args['tasks'].count()
    args['num_tasks'] = args['other_num']


    args['alltasks'] = True
    args['filters'] = get_task_filters(request)

    set_filter_message(request)

    return render_to_response('task_list.html', RequestContext(request, args))


@login_required
def user_all_tasks(request, assignee=False, userange=True):
    """
    Displays all of the tasks created by the 
    logged in user
    """

    args = {}
    args['tags'] = Tag.objects.filter(Q(owner=request.user) | Q(
        users=request.user) | Q(viewers=request.user)).order_by("name")

    if (not assignee):
        args['notodo'] = True
        tasks = apply_task_filter(
            request, ProjectTask.objects.filter(creator=request.user))
    else:
        tasks = apply_task_filter(
            request,
            ProjectTask.objects.filter(assigned=request.user)
        )

    set_filter_message(request)

    args['user'] = request.user
    args['projects'] = Project.objects.filter(
        Q(manager=request.user) | Q(members=request.user)).distinct()

    args['other_name'] = 'All Other Tasks'
    args['showmore'] = True

    if userange:
        args['tasks'] = tasks.filter(inProgress=False).filter(
            completed=False).order_by('-startDate').all()[0:5]
        args['task_wip'] = tasks.filter(inProgress=True).filter(
            completed=False).order_by('-startDate').all()[0:5]
        args['done_tasks'] = tasks.filter(
            completed=True).order_by('-startDate').all()[0:5]
    else:
        args['task_wip'] = tasks.filter(inProgress=True).filter(
            completed=False).order_by('-startDate').all()
        args['tasks'] = tasks.filter(inProgress=False).filter(
            completed=False).order_by('-startDate').all()

    args['done_num'] = tasks.filter(completed=True).count()
    args['wip_num'] = tasks.filter(
        inProgress=True).filter(completed=False).count()
    args['other_num'] = tasks.filter(
        inProgress=False).filter(completed=False).count()

    args['num_tasks'] = len(tasks)
    args['filters'] = get_task_filters(request)

    return render_to_response('task_list.html', RequestContext(request, args))


@login_required
def task_progress_toggle(request, task_id):
    """
    Toggles a task's in progress status

    Arguments:
            task_id: integer task ID to toggle
    """
    task = ProjectTask.objects.get(id=task_id)

    if (request.user in task.assigned.all() or request.user == task.creator):
        task.inProgress = not task.inProgress
        task.save()

        messages.info(request, "Task Updated.")

    if ('HTTP_REFERER' in request.META):
        return HttpResponseRedirect(request.META['HTTP_REFERER'])
    else:
        return HttpResponseRedirect('/projects/task/view/' + str(task_id))


@login_required
def assign_task_tag(request, task_id, tag_id=False):
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
        tags = Tag.objects.filter(
            Q(owner=request.user) | Q(users=request.user)).filter(visible=True)
        task = ProjectTask.objects.get(id=task_id)

        pageData = {}
        pageData['task'] = task
        pageData['tags'] = tags
        pageData['allowNew'] = True

        return render_to_response('tag_select.html', RequestContext(request, pageData))

    else:

        task = ProjectTask.objects.get(id=task_id)
        tag = Tag.objects.get(id=tag_id)

        if (request.user in tag.users.all() or request.user == tag.owner):

            task.tags.add(tag)
            task.save()

        return HttpResponseRedirect(returnUrl)


@login_required
def add_task(request, proj_id=False):
    """
    Provides a blank form for creating a new 
    task and the facilities for saving it and 
    redirecting to assign it to a project.
    """

    if request.method == "POST" and "useexisting" not in request.POST:

        form = EditTaskForm(request.POST)
        if form.is_valid():

            projTask = ProjectTask()
            projTask.summary = form.cleaned_data['summary']
            projTask.description = form.cleaned_data['description']
            projTask.creator = request.user

            projTask.save()

            projTask.assigned.add(request.user)
            projTask.save()

            if proj_id != False:
                project = Project.objects.get(id=proj_id)

                if request.user in project.members.all() or request.user == project.manager:
                    projTask.project = project
                    projTask.save()
                else:
                    messages.warning(
                        request, "You do not have the rights to add tasks to " + project.name)

            messages.info(request, "Task Saved.")

            return HttpResponseRedirect('/projects/addtotask/' + str(projTask.id))

        else:
            messages.error(request, "Please fill out both fields.")

            pageData = {}
            pageData['form'] = EditTaskForm(request.POST)

            return render_to_response('task_create.html', RequestContext(request, pageData))

    else:

        args = {}
        try:
            request.session['returnUrl'] = request.META['HTTP_REFERER']
        except:
            request.session['returnUrl'] = '/projects/usertasks'

        if (proj_id != False):
            args['project'] = project = Project.objects.get(id=proj_id)

        args['form'] = EditTaskForm()

        return render_to_response('task_create.html', RequestContext(request, args))


@login_required
def delete_task(request, task_id):
    """
    Deletes the selected task
    """
    task = ProjectTask.objects.get(id=task_id)

    if (request.user == task.creator):
        task.delete()
        messages.info(request, "Deleted task.")
        return HttpResponseRedirect('/projects/usertasks/')

    else:
        messages.error(
            request, "You do not have the rights to delete this task.")
        return HttpResponseRedirect('/projects/task/view/' + str(task_id))


@login_required
def untag_task(request, task_id, tag_id):
    tag = Tag.objects.get(id=tag_id)
    task = ProjectTask.objects.get(id=task_id)

    if (request.user in tag.users.all() or request.user == tag.owner):
        task.tags.remove(tag)
        messages.info(request, "Untagged task " + task.summary)
    else:
        messages.warning(request, "You are not allowed to remove this tag. ")

    return HttpResponseRedirect('/projects/task/view/' + str(task_id))


@login_required
def view_task(request, task_id):
    """
    Displays a chosen task
    """

    task = ProjectTask.objects.get(id=task_id)

    args = {}
    initialDict = {
        "summary": task.summary,
        "description": task.description,
    }

    form = EditTaskForm()
    form.initial = initialDict

    args['form'] = form
    args['openOn'] = [task.project]
    args['task'] = task
    args['members'] = task.assigned.all()
    args['user'] = request.user
    args['canEdit'] = (task.creator == request.user)
    args['isMember'] = (request.user in task.assigned.all())
    args['tags'] = task.tags.filter(Q(owner=request.user) | Q(
        users=request.user) | Q(viewers=request.user) | Q(public=True))
    args['yourTags'] = args['tags'].filter(
        Q(owner=request.user) | Q(users=request.user) | Q(viewers=request.user))

    args.update(csrf(request))

    args['add_member_form'] = AddMemberForm()

    return render_to_response('task_view.html', RequestContext(request, args))


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

    if (request.method == "POST" and task.creator == request.user):
        form = AddMemberForm(request.POST)
        if (form.is_valid()):
            username = form.cleaned_data['username']

            try:
                user = User.objects.get(username=username)

                if (user not in task.assigned.all()):
                    task.assigned.add(user)
                    task.save()
                    messages.info(
                        request, "Assigned " + user.username + " to task.")
            except:

                messages.error(
                    request, "User " + username + " is not a valid user.")

    return HttpResponseRedirect('/projects/task/view/' + str(task_id) + "/")


@login_required
def remove_task_member(request, task_id, user_id):
    """
    Removes a task member (assignee)

    Arguments:
            task_id - integer task ID
            user_id - integer user ID

    Returns:
            redirect back to the project view page 
    """
    task = ProjectTask.objects.get(id=task_id)
    user = User.objects.get(id=user_id)

    if (task.creator == request.user):
        task.assigned.remove(user)
        task.save()

        messages.info(request, "Unassigned " + user.username)

    return HttpResponseRedirect('/projects/task/view/' + str(task_id) + "/")


@login_required
def edit_task(request, task_id):
    """
    Provides a form populated with a task's data that 
    allows the task to be updated and saved.
    """
    task = ProjectTask.objects.get(id=task_id)

    if (request.method == "POST"):
        form = EditTaskForm(request.POST, instance=task)
        if form.is_valid() and request.user == task.creator:

            task.save()

            return HttpResponseRedirect('/projects/task/view/' + str(task.id) + "/")

        elif request.user != task.creator:
            messages.error(
                request, "You do not have permission to edit this task.")
            return HttpResponseRedirect('/projects/task/view/' + str(task.id) + "/")

        else:

            messages.error(request, "Please fill out both fields.")
            pageData = {}
            pageData['form'] = EditTaskForm(request.POST)
            pageData['task'] = ProjectTask.objects.get(id=task_id)
            return render_to_response('task_edit.html', RequestContext(request, pageData))

    else:

        form = EditTaskForm(instance=task)

        args = {}
        args['form'] = form
        args['task'] = task

        return render_to_response('task_edit.html', RequestContext(request, args))


@login_required
def my_todo(request):
    """
    Displays the My Todo page with the list of active 
    tasks the user has assigned to them.
    """

    return user_all_tasks(request, assignee=request.user)


def todo_by_status(request, status):

    return tasks_by_status(request, assignee=request.user, status=status)
