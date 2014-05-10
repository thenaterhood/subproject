from django.test import TestCase

from django.test.client import Client
from django.contrib.auth import get_user_model

from project.models import Project
from tasks.models import ProjectTask
from tagging.models import *
from tagging.views import *

class TagActions(TestCase):

    def setUp(self):
        joe = get_user_model().objects.create_user(
            username='joe', email=None, password='pass')
        bob = get_user_model().objects.create_user(
            username="bob", first_name="Bob", last_name="Herp", email="bob@joe.joe", password="pass")
        joeProject = Project.objects.create(
            name="Joe's Project", manager=joe, description="Belongs to Joe", status="None", phase="None")
        bobProject = Project.objects.create(
            name="Bob's Project", manager=bob, description="Belongs to Joe", status="None", phase="None")
        joeTask = ProjectTask.objects.create(
            summary="Joe's Task", creator=joe, description="Joe's")
        bobTask = ProjectTask.objects.create(
            summary="Bob's Task", creator=bob, description="Bob's")

        joeTag = Tag.objects.create(
            name="Joe's Tag", description="Joe's", owner=joe)

        self.client = Client()
        self.client.login(username="joe", password="pass")

    def test_tag_untag_task(self):
        self.client.get('/projects/task/1/addtag/1/')

        tag = Tag.objects.get(id=1)
        task = ProjectTask.objects.get(id=1)

        self.assertTrue(tag in task.tags.all())

        self.client.get('/projects/task/1/untag/1/')
        task = ProjectTask.objects.get(id=1)

        self.assertFalse(tag in task.tags.all())

    def test_tag_untag_project(self):
        self.client.get('/projects/1/addtag/1/')

        tag = Tag.objects.get(id=1)
        project = Project.objects.get(id=1)

        self.assertTrue(tag in project.tags.all())

        self.client.get('/projects/1/untag/1/')
        project = Project.objects.get(id=1)

        self.assertFalse(tag in project.tags.all())

    def test_create_private_tag(self):

        tagData = {}
        tagData['name'] = 'joetag'
        tagData['description'] = "Joe's Tag"

        response = self.client.post('/projects/newtag/', tagData)

        tag = Tag.objects.filter(name='joetag')

        self.assertEqual(tag.count(), 1)
        self.assertFalse(tag[0].public)

    def test_create_public_tag(self):

        tagData = {}
        tagData['name'] = 'joetag'
        tagData['description'] = "Joe's Tag"
        tagData['public'] = True

        response = self.client.post('/projects/newtag/', tagData)

        tag = Tag.objects.filter(name='joetag')

        self.assertEqual(tag.count(), 1)
        self.assertTrue(tag[0].public)

    def test_delete_tag(self):

        response = self.client.get('/projects/tag/delete/1/')

        tags = Tag.objects.filter(name="Joe's Tag")

        self.assertEqual(tags.count(), 0)

    def test_add_remove_viewer(self):

        bob = User.objects.get(username='bob')

        response = Client().post(
            '/projects/tag/addviewer/1/', {'username': 'bob'})

        self.assertFalse(bob in Tag.objects.get(id=1).viewers.all())

        response = self.client.post(
            '/projects/tag/addviewer/1/', {'username': 'bob'})
        self.assertTrue(bob in Tag.objects.get(id=1).viewers.all())

        response = self.client.get('/projects/tag/1/revokeviewer/2/')
        self.assertFalse(bob in Tag.objects.get(id=1).viewers.all())

    def test_add_remove_user(self):

        bob = User.objects.get(username='bob')

        response = Client().post(
            '/projects/tag/adduser/1/', {'username': 'bob'})

        self.assertFalse(bob in Tag.objects.get(id=1).users.all())

        response = self.client.post(
            '/projects/tag/adduser/1/', {'username': 'bob'})
        self.assertTrue(bob in Tag.objects.get(id=1).users.all())

        response = self.client.get('/projects/tag/1/revokeuser/2/')
        self.assertFalse(bob in Tag.objects.get(id=1).users.all())

    def test_view_tag(self):

        response = self.client.get('/projects/tags/1/')

        self.assertTrue('tag' in response.context)
        tag = Tag.objects.get(id=1)

        self.assertEqual(response.context['tag'], tag)

    def test_list_tags(self):

        response = self.client.get('/projects/tags/')

        self.assertTrue('tags' in response.context)
        self.assertTrue(len(response.context['tags']) > 0)
