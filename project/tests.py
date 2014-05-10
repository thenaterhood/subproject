"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from project.models import *
from project.views import *

from django.test.client import Client
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

class ProjectView_Update(TestCase):

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

    def test_show_browser(self):
        response = self.client.get('/projects/browser/')

        self.assertTrue('projects' in response.context)

        response = self.client.get('/projects/browser/1/')

        self.assertTrue('projects' in response.context)
        self.assertTrue('selected' in response.context)
        self.assertEqual(
            response.context['selected'], Project.objects.get(id=1))

    def test_show_panels(self):
        response = self.client.get('/projects/outline/')

        self.assertTrue('panel1' in response.context)

        response = self.client.get('/projects/outline/?pos=1')
        self.assertTrue('panel1' in response.context)
        self.assertTrue('panel2' in response.context)

        response = self.client.get('/projects/outline/?pos=1,1')
        self.assertTrue('panel1' in response.context)
        self.assertTrue('panel2' in response.context)
        self.assertTrue('panel3' in response.context)

    def test_login_success(self):

        c = Client()
        response = c.post(
            '/accounts/login/', {'username': 'joe', 'password': 'pass'})

        self.assertEqual(response.status_code, 200)

    def test_project_home(self):
        response = self.client.get('/')

        self.assertTrue(response.status_code in [301, 200, 302])

        self.assertTrue('total_projects' in response.context)
        self.assertTrue('managed_projects' in response.context)
        self.assertEqual(response.context['managed_projects'], 1)
        self.assertTrue('total_worklogs' in response.context)
        self.assertTrue('total_tasks' in response.context)
        self.assertTrue('active_tasks' in response.context)
        self.assertTrue('total_time' in response.context)
        self.assertTrue('start_date' in response.context)
        self.assertTrue('numTasks' in response.context)
        self.assertTrue('avg_task_time' in response.context)
        self.assertTrue('end_date' in response.context)

    def test_project_view(self):

        response = self.client.get('/projects/view/1/')

        self.assertTrue(response.status_code in [301, 200])

        self.assertTrue('project' in response.context)
        self.assertEqual(response.context['project'].name, "Joe's Project")
        self.assertTrue('worklogs' in response.context)
        self.assertTrue('tasks' in response.context)

    def test_project_update(self):

        response = self.client.post('/projects/edit/1/', {'name': 'A Project', 'phase': "phased", 'status': 'statused',
                                                          'description': 'changed'})

        response = self.client.get('/projects/view/1/')

        self.assertEqual(response.context['project'].name, "A Project")
        self.assertEqual(response.context['project'].phase, 'phased')
        self.assertEqual(response.context['project'].status, 'statused')
        self.assertEqual(response.context['project'].description, 'changed')

    def test_project_update_bad_data(self):

        response = self.client.post('/projects/edit/1/', {'name': 'A Project', 'status': 'statused',
                                                          'description': 'changed'})

        response = self.client.get('/projects/view/1/')

        self.assertEqual(response.context['project'].name, "Joe's Project")

    def test_project_update_bad_user(self):
        c = Client()
        c.login(username="bob", password="pass")

        response = c.post('/projects/edit/1/', {'name': 'A Project', 'phase': "phased", 'status': 'statused',
                                                'description': 'changed'})

        response = c.get('/projects/view/1/')

        self.assertEqual(response.context['project'].name, "Joe's Project")

    def test_project_close(self):
        c = Client()
        c.login(username="joe", password="pass")

        response = c.get('/projects/toggle/1/')

        project = Project.objects.get(id=1)
        self.assertTrue(not project.active)

        response = c.get('/projects/toggle/1/')
        self.assertTrue(not project.active)

    def test_project_close_bad_user(self):
        c = Client()
        c.login(username="bob", password="pass")

        response = c.get('/projects/toggle/1/')

        project = Project.objects.get(id=1)
        self.assertTrue(project.active)

    def test_project_add_member(self):

        response = self.client.post(
            '/projects/addmember/1/', {'username': 'bob'})

        project = Project.objects.get(id=1)
        bob = User.objects.get(username="bob")

        self.assertTrue(bob in project.members.all())

    def test_project_add_member_bad_user(self):
        c = Client()
        c.login(username="bob", password="pass")

        response = c.post('/projects/addmember/1/', {'username': 'bob'})

        project = Project.objects.get(id=1)
        bob = User.objects.get(username="bob")

        self.assertFalse(bob in project.members.all())

    def test_project_remove_member(self):

        response = self.client.post(
            '/projects/addmember/1/', {'username': 'bob'})

        project = Project.objects.get(id=1)
        bob = User.objects.get(username="bob")

        self.assertTrue(bob in project.members.all())

        response = self.client.post('/projects/removemember/1/2/')

        self.assertFalse(bob in project.members.all())

    def test_project_remove_member_bad_user(self):

        response = self.client.post(
            '/projects/addmember/1/', {'username': 'bob'})
        response = self.client.post(
            '/projects/addmember/1/', {'username': 'joe'})

        project = Project.objects.get(id=1)
        bob = User.objects.get(username="bob")
        joe = User.objects.get(username="joe")

        self.assertTrue(bob in project.members.all())

        self.client.logout()
        self.client.login(username="bob", password="pass")

        response = self.client.post('/projects/removemember/1/1/')

        project = Project.objects.get(id=1)

        self.assertTrue(joe in project.members.all())

    def test_project_assign_remove_child(self):
        c = Client()
        c.login(username="joe", password="pass")

        response = c.post('/projects/1/assignchild/2/')

        project1 = Project.objects.get(id=1)
        project2 = Project.objects.get(id=2)

        self.assertTrue(project2 in project1.subprojects.all())
        self.assertTrue(project1 in project2.parents.all())

        response = c.post('/projects/children/1/')
        self.assertTrue(project2 in response.context['projects'])

        response = c.post('/projects/parents/2/')
        self.assertTrue(project1 in response.context['projects'])

        c.logout()
        c.login(username="bob", password="pass")
        response = c.post('/projects/totop/2/')

        project1 = Project.objects.get(id=1)
        project2 = Project.objects.get(id=2)

        self.assertFalse(project2 in project1.subprojects.all())
        self.assertFalse(project1 in project2.parents.all())

    def test_create_project(self):

        pdata = {}
        pdata['name'] = "My New Project"
        pdata['status'] = "My Status"
        pdata['phase'] = "My Phase"
        pdata['description'] = "My description"

        c = Client()

        response = c.post('/projects/create/', pdata)

        self.assertEqual(
            Project.objects.filter(name="My New Project").count(), 0)

        c.login(username='joe', password='pass')
        response = c.post('/projects/create/', pdata)

        self.assertEqual(
            Project.objects.filter(name="My New Project").count(), 1)
        p = Project.objects.get(name="My New Project")

        self.assertEqual(p.name, "My New Project")
        self.assertEqual(p.status, "My Status")
        self.assertEqual(p.phase, "My Phase")
        self.assertEqual(p.description, "My description")

    def test_list_projects(self):
        c = Client()
        c.login(username='joe', password='pass')

        response = c.get('/projects/')

        self.assertTrue('owned' in response.context)
        self.assertEqual(len(response.context['owned']), 1)


class DataImport(TestCase):

    def setUp(self):
        joe = get_user_model().objects.create_user(
            username='joe', email=None, password='pass')
        bob = get_user_model().objects.create_user(
            username="bob", first_name="Bob", last_name="Herp", email="bob@joe.joe", password="pass")
        #joeProject=Project.objects.create(name="Joe's Project",manager=joe,description="Belongs to Joe", status="None", phase="None")
        #bobProject=Project.objects.create(name="Bob's Project",manager=bob,description="Belongs to Joe", status="None", phase="None")

        self.client = Client()
        self.client.login(username="joe", password="pass")

    def test_clean_project_csv_import(self):
        joe = User.objects.get(username='joe')

        initialNum = Project.objects.filter(manager=joe).count()
        # Clean file contains 11 items
        with open('test_files/clean_projects.csv') as importCsv:
            response = self.client.post('/projects/importcsv/projects/',
                                        {'file': SimpleUploadedFile(importCsv.name, bytes(importCsv.read(), "UTF-8"), content_type='text/csv')})

        afterNum = Project.objects.filter(manager=joe).count()

        self.assertEqual(afterNum - 11, initialNum)

        imports = Project.objects.filter(manager=joe).filter(status='imported')

        for i in imports:
            self.assertEqual(i.phase, "Development")
            self.assertTrue('[Imported Project]' in i.description)

    def test_clean_worklog_csv_import(self):
        joe = User.objects.get(username='joe')

        with open('test_files/clean_projects.csv') as importCsv:
            response = self.client.post('/projects/importcsv/projects/',
                                        {'file': SimpleUploadedFile(importCsv.name, bytes(importCsv.read(), "UTF-8"), content_type='text/csv')})

        initialNum = Worklog.objects.filter(owner=joe).count()

        with open('test_files/clean_worklogs.csv') as importCsv:
            response = self.client.post('/projects/importcsv/work/',
                                        {'file': SimpleUploadedFile(importCsv.name, bytes(importCsv.read(), "UTF-8"), content_type='text/csv')})

        afterNum = Worklog.objects.filter(owner=joe).count()
        imports = Worklog.objects.filter(owner=joe)

        self.assertEqual(afterNum - 12, initialNum)

        for i in imports:
            self.assertEqual(i.hours, 1)
            self.assertEqual(i.description, "some added work")

    def test_headless_project_csv_import(self):
        joe = User.objects.get(username='joe')

        initialNum = Project.objects.filter(manager=joe).count()
        # Clean file contains 11 items
        with open('test_files/headless_projects.csv') as importCsv:
            response = self.client.post('/projects/importcsv/projects/',
                                        {'file': SimpleUploadedFile(importCsv.name, bytes(importCsv.read(), "UTF-8"), content_type='text/csv')})

        afterNum = Project.objects.filter(manager=joe).count()

        self.assertEqual(afterNum, initialNum)

        imports = Project.objects.filter(manager=joe).filter(status='imported')

        self.assertEqual(imports.count(), 0)

    def test_headless_worklog_csv_import(self):
        joe = User.objects.get(username='joe')

        with open('test_files/headless_projects.csv') as importCsv:
            response = self.client.post('/projects/importcsv/projects/',
                                        {'file': SimpleUploadedFile(importCsv.name, bytes(importCsv.read(), "UTF-8"), content_type='text/csv')})

        initialNum = Worklog.objects.filter(owner=joe).count()

        with open('test_files/clean_worklogs.csv') as importCsv:
            response = self.client.post('/projects/importcsv/work/',
                                        {'file': SimpleUploadedFile(importCsv.name, bytes(importCsv.read(), "UTF-8"), content_type='text/csv')})

        afterNum = Worklog.objects.filter(owner=joe).count()
        imports = Worklog.objects.filter(owner=joe)

        self.assertEqual(afterNum, initialNum)

    def test_badquote_project_csv_import(self):
        joe = User.objects.get(username='joe')

        initialNum = Project.objects.filter(manager=joe).count()
        # Clean file contains 11 items
        with open('test_files/badquotes_projects.csv') as importCsv:
            response = self.client.post('/projects/importcsv/projects/',
                                        {'file': SimpleUploadedFile(importCsv.name, bytes(importCsv.read(), "UTF-8"), content_type='text/csv')})

        afterNum = Project.objects.filter(manager=joe).count()

        self.assertEqual(afterNum - 9, initialNum)

        imports = Project.objects.filter(manager=joe).filter(status='imported')

        # 3 rows are misquoted and cause the status to be
        # misread.
        self.assertEqual(imports.count() - 11 + 3, initialNum)

    def test_badquote_worklog_csv_import(self):
        joe = User.objects.get(username='joe')

        with open('test_files/badquotes_projects.csv') as importCsv:
            response = self.client.post('/projects/importcsv/projects/',
                                        {'file': SimpleUploadedFile(importCsv.name, bytes(importCsv.read(), "UTF-8"), content_type='text/csv')})

        initialNum = Worklog.objects.filter(owner=joe).count()

        with open('test_files/clean_worklogs.csv') as importCsv:
            response = self.client.post('/projects/importcsv/work/',
                                        {'file': SimpleUploadedFile(importCsv.name, bytes(importCsv.read(), "UTF-8"), content_type='text/csv')})

        afterNum = Worklog.objects.filter(owner=joe).count()
        imports = Worklog.objects.filter(owner=joe)

        # 3 rows are misquoted, so those rows should fail
        # We add them back on.
        self.assertEqual(afterNum - 13 + 3, initialNum)

    def test_fieldsmissing_project_csv_import(self):
        joe = User.objects.get(username='joe')

        initialNum = Project.objects.filter(manager=joe).count()
        # Clean file contains 11 items
        with open('test_files/missingfields_projects.csv') as importCsv:
            response = self.client.post('/projects/importcsv/projects/',
                                        {'file': SimpleUploadedFile(importCsv.name, bytes(importCsv.read(), "UTF-8"), content_type='text/csv')})

        afterNum = Project.objects.filter(manager=joe).count()

        self.assertEqual(afterNum - 11, initialNum)

        imports = Project.objects.filter(manager=joe).filter(status='imported')

        # The status field is missing on some or
        # has been non-catastrophically misinterpreted.
        self.assertEqual(imports.count() - 11 + 3, 0)

    def test_fieldsmissing_worklog_csv_import(self):
        joe = User.objects.get(username='joe')

        with open('test_files/missingfields_projects.csv') as importCsv:
            response = self.client.post('/projects/importcsv/projects/',
                                        {'file': SimpleUploadedFile(importCsv.name, bytes(importCsv.read(), "UTF-8"), content_type='text/csv')})

        initialNum = Worklog.objects.filter(owner=joe).count()

        with open('test_files/clean_worklogs.csv') as importCsv:
            response = self.client.post('/projects/importcsv/work/',
                                        {'file': SimpleUploadedFile(importCsv.name, bytes(importCsv.read(), "UTF-8"), content_type='text/csv')})

        afterNum = Worklog.objects.filter(owner=joe).count()
        imports = Worklog.objects.filter(owner=joe)

        self.assertEqual(afterNum - 10, initialNum)
