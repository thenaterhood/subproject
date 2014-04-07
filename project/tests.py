"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from user.models import *
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

        self.assertEqual(afterNum - 11, initialNum)

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
