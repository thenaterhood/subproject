from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import F
from django.db.models import Q
from django.contrib import messages

from copy import deepcopy

from tagging.models import Tag
from filters.views import set_filter_message

from user.forms import AddMemberForm
from tagging.forms import AddTagForm

from project.models import Project
from tasks.models import ProjectTask


@login_required
def list_tags(request):
    """
    Displays a list of the user's tags
    """

    tags = Tag.objects.filter(Q(owner=request.user) | Q(
        users=request.user) | Q(viewers=request.user)).filter(visible=True)
    set_filter_message(request)

    pageData = {}
    pageData['tags'] = tags
    pageData['user'] = request.user

    return render_to_response('tag_list.html', RequestContext(request, pageData))


@login_required
def add_tag(request, tag_id=False, project_id=False, task_id=False):
    """
    Provides a page where tags can be
    created by the user.
    """
    if request.method == 'POST':
        postData = deepcopy(request.POST)

        if ('public' not in request.POST):
            postData['public'] = 'off'

        form = AddTagForm(postData)

        if form.is_valid():

            if (not tag_id):
                newTag = Tag()
            else:
                newTag = Tag.objects.get(id=tag_id)

            newTag.name = form.cleaned_data['name']
            newTag.description = form.cleaned_data['description']
            newTag.public = form.cleaned_data['public']
            newTag.owner = request.user

            if ('public' not in request.POST):
                newTag.public = False

            newTag.save()

            if (task_id):
                task = ProjectTask.objects.get(id=task_id)
                task.tags.add(newTag)
                task.save()
            if (project_id):
                project = Project.objects.get(id=project_id)
                project.tags.add(newTag)
                project.save()

            if ('returnUrl' in request.session):
                return HttpResponseRedirect(request.session['returnUrl'])
            else:
                return HttpResponseRedirect('/tags/' + str(newTag.id))

        else:

            pageData = {}
            pageData['form'] = form
            pageData['postTo'] = request.get_full_path()
            messages.warning(request, "Please check your inputs.")
            return render_to_response('tag_create.html', RequestContext(request, pageData))

    else:
        form = AddTagForm()
        args = {}
        args['form'] = form
        args['postTo'] = request.get_full_path()
        return render_to_response('tag_create.html', RequestContext(request, args))


@login_required
def view_tag(request, tag_id):
    """
    Displays a tag
    """
    tag = Tag.objects.get(id=tag_id)

    if (request.user == tag.owner
            or request.user in tag.viewers.all()
            or request.user in tag.users.all()
            or tag.public):

        pageData = {}
        pageData['tag'] = tag
        pageData['canEdit'] = (
            request.user == tag.owner or request.user in tag.users.all())
        pageData['viewers'] = tag.viewers.all()
        pageData['users'] = tag.users.all()
        pageData['public'] = tag.public
        pageData['add_user_form'] = AddMemberForm()
        form = AddTagForm()
        initialDict = {
            'public': tag.public,
            'name': tag.name,
            'description': tag.description
        }
        form.initial = initialDict
        pageData['form'] = form

        return render_to_response('tag_view.html', RequestContext(request, pageData))

    else:
        return HttpResponseRedirect('/tags/')


@login_required
def delete_tag(request, tag_id):
    """
    Deletes a tag from the system.

    Arguments:
            tag_id - integer tag ID
    """
    tag = Tag.objects.get(id=tag_id)
    if (request.user == tag.owner):
        tag.delete()

        messages.info(request, "Deleted tag " + tag.name)

    return HttpResponseRedirect('/')


@login_required
def toggle_tag_user(request, tag_id, user_id=False):
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
    tag = Tag.objects.get(id=tag_id)

    if (request.user == tag.owner or request.user in tag.users.all()):

        if (not user_id):
            form = AddMemberForm(request.POST)
            form.is_valid()
            user = User.objects.get(username=form.cleaned_data['username'])
        else:
            user = User.objects.get(id=user_id)

        if (user in tag.users.all()):
            tag.users.remove(user)
        else:
            tag.users.add(user)

        tag.save()

    messages.info(request, "Updated " + str(user) + "'s tag user status.")

    return HttpResponseRedirect('/tags/' + str(tag_id))


@login_required
def toggle_tag_viewer(request, tag_id, user_id=False):
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
    tag = Tag.objects.get(id=tag_id)

    if ((request.user == tag.owner or request.user in tag.users.all())):
        if (not user_id):
            form = AddMemberForm(request.POST)
            form.is_valid()
            user = User.objects.get(username=form.cleaned_data['username'])
        else:
            user = User.objects.get(id=user_id)

        if (user in tag.viewers.all()):
            tag.viewers.remove(user)
        else:
            tag.viewers.add(user)

        tag.save()

    messages.info(request, "Updated " + str(user) + "'s tag viewer status.")
    return HttpResponseRedirect('/tags/' + str(tag_id))
