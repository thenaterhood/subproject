from django.test import TestCase

from django.test.client import Client
from django.contrib.auth import get_user_model

from project.models import Project
from worklogs.models import *
from worklogs.views import *

class WorklogActions(TestCase):

    def setUp(self):
        joe = get_user_model().objects.create_user(
            username='joe', email=None, password='pass')
        bob = get_user_model().objects.create_user(
            username="bob", first_name="Bob", last_name="Herp", email="bob@joe.joe", password="pass")
        joeProject = Project.objects.create(
            name="Joe's Project", manager=joe, description="Belongs to Joe", status="None", phase="None")
        bobProject = Project.objects.create(
            name="Bob's Project", manager=bob, description="Belongs to Joe", status="None", phase="None")

        self.client = Client()
        self.client.login(username="joe", password="pass")

    def test_add_edit_worklog(self):

        worklog = {}
        worklog['summary'] = "Joe's Work"
        worklog['description'] = "Joe's"
        worklog['minutes'] = 0
        worklog['hours'] = 1

        response = self.client.post('/projects/addwork/1/', worklog)

        logs = Worklog.objects.filter(summary="Joe's Work")
        self.assertTrue(logs.count() > 0)

        log = logs[0]

        self.assertEqual(log.summary, "Joe's Work")
        self.assertEqual(log.description, "Joe's")
        self.assertEqual(log.hours, 1)

        worklog['summary'] = "Just Joe"

        response = self.client.post('/projects/work/edit/1/', worklog)
        logs = Worklog.objects.filter(summary="Just Joe")
        self.assertTrue(logs.count() > 0)

    def test_view_worklog(self):

        worklog = {}
        worklog['summary'] = "Joe's Work"
        worklog['description'] = "Joe's"
        worklog['minutes'] = 0
        worklog['hours'] = 1

        response = self.client.post('/projects/addwork/1/', worklog)
        response = self.client.get('/projects/work/view/1/')

        log = Worklog.objects.get(summary="Joe's Work")

        self.assertTrue('worklog' in response.context)
        self.assertEqual(log, response.context['worklog'])
