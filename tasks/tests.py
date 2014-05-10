from django.test import TestCase

from django.test.client import Client
from django.contrib.auth import get_user_model

from project.models import Project
from tasks.models import ProjectTask
from tasks.views import *

class TaskActions(TestCase):

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

        joeTask.project = joeProject
        joeTask.save()

        joeProject.members.add(joe)

        self.client = Client()
        self.client.login(username="joe", password="pass")

    def test_remove_add_project_task(self):
        self.client.get('/projects/1/unassigntask/1/')

        task = ProjectTask.objects.get(id=1)
        project = Project.objects.get(id=1)

        self.assertTrue(task.project == None)

        self.client.get('/projects/1/assigntask/1/')

        task = ProjectTask.objects.get(id=1)

        self.assertTrue(project == task.project)
        self.client.get('/projects/1/unassigntask/1/')

        # This tests the reverse - the previous tests
        # the path of choosing a task, starting at the
        # project view page. Below starts at the task
        # page and allows a project to be selected instead
        # to assign the task to.

        self.client.get('/projects/addtotask/1/1/')
        task = ProjectTask.objects.get(id=1)

        self.assertTrue(task.project == project)

    def test_task_to_subproject(self):
        self.client.get('/projects/task/tosubproject/1/')

        task = ProjectTask.objects.filter(summary="Joe's Task")
        self.assertEqual(task.count(), 0)

        project = Project.objects.filter(name="Joe's Task")
        parentProject = Project.objects.get(name="Joe's Project")

        self.assertTrue(project.count() > 0)
        self.assertEqual(project[0].description, "Joe's")
        self.assertTrue(parentProject in project[0].parents.all())
        self.assertTrue(project[0] in parentProject.subprojects.all())

    def test_create_delete_task(self):

        tdata = {}
        tdata['summary'] = "My Task"
        tdata['description'] = "Just Mine"

        c = Client()
        response = c.post('/projects/addtask/', tdata)

        self.assertEqual(
            ProjectTask.objects.filter(summary="Just Mine").count(), 0)

        c.login(username='joe', password='pass')

        t = ProjectTask.objects.get(id=1)

        response = c.post('/projects/addtask/', tdata)
        self.assertEqual(
            ProjectTask.objects.filter(summary="My Task").count(), 1)

        t = ProjectTask.objects.get(summary="My Task")
        tid = t.id

        self.assertEqual(t.summary, "My Task")
        self.assertEqual(t.description, "Just Mine")

        response = c.get('/projects/task/delete/' + str(tid) + '/')

        self.assertEqual(
            ProjectTask.objects.filter(summary="My Task").count(), 0)

    def test_edit_task(self):

        tdata = {}
        tdata['summary'] = "My Task"
        tdata['description'] = "Just Mine"

        c = Client()
        response = c.post('/projects/task/edit/1/', tdata)

        t = ProjectTask.objects.get(id=1)

        self.assertEqual(t.summary, "Joe's Task")

        response = self.client.post('/projects/task/edit/1/', tdata)

        t = ProjectTask.objects.get(id=1)

        self.assertEqual(t.summary, "My Task")

    def test_create_task_and_assign(self):

        tdata = {}
        tdata['summary'] = "My Task"
        tdata['description'] = "Just Mine"

        t = ProjectTask.objects.get(id=1)

        response = self.client.post('/projects/addtask/1/', tdata)
        self.assertEqual(
            ProjectTask.objects.filter(summary="My Task").count(), 1)

        t = ProjectTask.objects.get(summary="My Task")

        self.assertEqual(t.summary, "My Task")
        self.assertEqual(t.description, "Just Mine")

        p = Project.objects.get(id=1)

        self.assertTrue(p == t.project)

    def test_user_task_show(self):

        bobTask = ProjectTask.objects.get(id=2)
        joeTask = ProjectTask.objects.get(id=1)

        joe = User.objects.get(username='joe')
        bobProject = Project.objects.get(id=2)

        bobTask.assigned.add(joe)
        bobTask.project = bobProject
        bobTask.save()

        response = self.client.get('/projects/todo/')

        self.assertTrue('tasks' in response.context)
        self.assertTrue(bobTask in response.context['tasks'])

        response = self.client.get('/projects/usertasks/')

        self.assertTrue('tasks' in response.context)
        self.assertTrue(joeTask in response.context['tasks'])

    def test_task_view(self):

        task = ProjectTask.objects.get(id=1)

        response = self.client.get('/projects/task/view/1/')

        self.assertTrue('task' in response.context)
        self.assertEqual(response.context['task'], task)

    def test_open_close_task(self):
        response = self.client.get('/projects/task/close/1/')

        task = ProjectTask.objects.get(id=1)
        project = Project.objects.get(id=1)

        self.assertTrue(task.completed)

        response = self.client.get('/projects/task/open/1/')

        task = ProjectTask.objects.get(id=1)
        self.assertFalse(task.completed)

    def test_wip_toggle(self):

        response = self.client.get('/projects/task/inprogress/1/')

        joeProject = ProjectTask.objects.get(id=1)

        self.assertTrue(joeProject.inProgress)

        response = self.client.get('/projects/task/inprogress/1/')

        joeProject = ProjectTask.objects.get(id=1)

        self.assertFalse(joeProject.inProgress)

    def test_add_remove_assignee(self):

        bob = User.objects.get(username="bob")

        response = self.client.post(
            '/projects/task/addmember/1/', {'username': 'bob'})
        self.assertTrue(bob in ProjectTask.objects.get(id=1).assigned.all())

        response = self.client.get('/projects/task/removemember/1/2/')
        self.assertFalse(bob in ProjectTask.objects.get(id=1).assigned.all())
