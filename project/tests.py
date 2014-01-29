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

class ProjectView_Update(TestCase):

	def setUp(self):
		joe= get_user_model().objects.create_user(username='joe', email=None, password='pass')
		bob= get_user_model().objects.create_user(username="bob", first_name="Bob", last_name="Herp", email="bob@joe.joe", password="pass")
		joeProject=Project.objects.create(name="Joe's Project",manager=joe,description="Belongs to Joe", status="None", phase="None")
		bobProject=Project.objects.create(name="Bob's Project",manager=bob,description="Belongs to Joe", status="None", phase="None")


	def test_login_success(self):

		c = Client()
		response = c.post('/accounts/login/', {'username': 'joe', 'password': 'pass'})

		self.assertEqual( response.status_code, 200 )


	def test_project_home(self):
		c = Client()
		self.assertTrue( c.login(username='joe', password='pass') ) 

		response = c.get('/')

		self.assertTrue( response.status_code in [301,200,302] )

		self.assertTrue( 'total_projects' in response.context )
		self.assertTrue( 'managed_projects' in response.context )
		self.assertEqual( response.context['managed_projects'], 1 )
		self.assertTrue( 'total_worklogs' in response.context )
		self.assertTrue( 'total_tasks' in response.context )
		self.assertTrue( 'active_tasks' in response.context )
		self.assertTrue( 'total_time' in response.context )
		self.assertTrue( 'start_date' in response.context )
		self.assertTrue( 'numTasks' in response.context )
		self.assertTrue( 'avg_task_time' in response.context )
		self.assertTrue( 'end_date' in response.context )

	def test_project_view(self):
		c = Client()
		c.login( username='joe', password='pass' )

		response = c.get('/projects/view/1/')

		self.assertTrue( response.status_code in [301,200] )

		self.assertTrue( 'project' in response.context )
		self.assertEqual( response.context['project'].name, "Joe's Project" )
		self.assertTrue( 'worklogs' in response.context )
		self.assertTrue( 'tasks' in response.context )


	def test_project_update( self ):
		c = Client()
		c.login( username="joe", password='pass' )

		response = c.post('/projects/edit/1/', {'name':'A Project', 'phase':"phased", 'status':'statused',
			'description':'changed'} )

		response = c.get('/projects/view/1/')

		self.assertEqual( response.context['project'].name, "A Project")
		self.assertEqual( response.context['project'].phase, 'phased')
		self.assertEqual( response.context['project'].status, 'statused')
		self.assertEqual( response.context['project'].description, 'changed' )

	def test_project_update_bad_data( self ):
		c = Client()
		c.login( username='joe', password='pass' )
		response = c.post('/projects/edit/1/', {'name':'A Project', 'status':'statused',
			'description':'changed'} )

		response = c.get('/projects/view/1/')

		self.assertEqual( response.context['project'].name, "Joe's Project")


	def test_project_update_bad_user( self ):
		c = Client()
		c.login( username="bob", password="pass" )

		response = c.post('/projects/edit/1/', {'name':'A Project', 'phase':"phased", 'status':'statused',
			'description':'changed'} )

		response = c.get('/projects/view/1/')

		self.assertEqual( response.context['project'].name, "Joe's Project")

	def test_project_close( self ):
		c = Client()
		c.login( username="joe", password="pass" )

		response = c.get('/projects/toggle/1/')

		project = Project.objects.get( id=1 )
		self.assertTrue( not project.active )

		response = c.get('/projects/toggle/1/')
		self.assertTrue( not project.active )

	def test_project_close_bad_user( self ):
		c = Client()
		c.login( username="bob", password="pass" )

		response = c.get('/projects/toggle/1/')

		project = Project.objects.get( id=1 )
		self.assertTrue( project.active )

	def test_project_add_member( self ):
		c = Client()
		c.login( username="joe", password="pass" )

		response = c.post('/projects/addmember/1/', {'username':'bob'} )

		project = Project.objects.get( id=1 )
		bob = User.objects.get( username="bob" )

		self.assertTrue( bob in project.members.all() )

	def test_project_add_member_bad_user( self ):
		c = Client()
		c.login( username="bob", password="pass" )

		response = c.post('/projects/addmember/1/', {'username':'bob'} )

		project = Project.objects.get( id=1 )
		bob = User.objects.get( username="bob" )

		self.assertFalse( bob in project.members.all() )

	def test_project_remove_member( self ):
		c = Client()
		c.login( username="joe", password="pass" )

		response = c.post('/projects/addmember/1/', {'username':'bob'} )

		project = Project.objects.get( id=1 )
		bob = User.objects.get( username="bob" )

		self.assertTrue( bob in project.members.all() )

		response = c.post('/projects/removemember/1/2/')

		self.assertFalse( bob in project.members.all() )

	def test_project_remove_member_bad_user( self ):
		c = Client()
		c.login( username="joe", password="pass" )

		response = c.post('/projects/addmember/1/', {'username':'bob'} )
		response = c.post('/projects/addmember/1/', {'username':'joe'} )

		project = Project.objects.get( id=1 )
		bob = User.objects.get( username="bob" )
		joe = User.objects.get( username="joe" )


		self.assertTrue( bob in project.members.all() )

		c.logout()
		c.login( username="bob", password="pass" )

		response = c.post('/projects/removemember/1/1/')

		project = Project.objects.get( id=1 )

		self.assertTrue( joe in project.members.all() )

	def test_project_assign_remove_child( self ):
		c = Client()
		c.login( username="joe", password="pass" )

		response = c.post('/projects/1/assignchild/2/')

		project1 = Project.objects.get( id=1 )
		project2 = Project.objects.get( id=2 )

		self.assertTrue( project2 in project1.subprojects.all() )
		self.assertTrue( project1 in project2.parents.all() )

		c.logout()
		c.login( username="bob", password="pass")
		response = c.post('/projects/totop/2/')

		project1 = Project.objects.get( id=1 )
		project2 = Project.objects.get( id=2 )

		self.assertFalse( project2 in project1.subprojects.all() )
		self.assertFalse( project1 in project2.parents.all() )

	def test_create_project( self ):

		pdata = {}
		pdata['name'] = "My New Project"
		pdata['status'] = "My Status"
		pdata['phase'] = "My Phase"
		pdata['description'] = "My description"

		c = Client()

		response = c.post('/projects/create/', pdata )

		self.assertEqual( Project.objects.filter(name="My New Project").count(), 0 )

		c.login( username='joe', password='pass')
		response = c.post('/projects/create/', pdata )

		self.assertEqual( Project.objects.filter(name="My New Project").count(), 1 )
		p = Project.objects.get( name="My New Project" )

		self.assertEqual( p.name, "My New Project" )
		self.assertEqual( p.status, "My Status" )
		self.assertEqual( p.phase, "My Phase" )
		self.assertEqual( p.description, "My description" )

	def test_list_projects(self):
		c = Client()
		c.login( username='joe', password='pass')

		response = c.get('/projects/')

		self.assertTrue( 'owned' in response.context )
		self.assertEqual( len(response.context['owned']), 1 )

class TaskActions(TestCase):

	def setUp(self):
		joe= get_user_model().objects.create_user(username='joe', email=None, password='pass')
		bob= get_user_model().objects.create_user(username="bob", first_name="Bob", last_name="Herp", email="bob@joe.joe", password="pass")
		joeProject=Project.objects.create(name="Joe's Project",manager=joe,description="Belongs to Joe", status="None", phase="None")
		bobProject=Project.objects.create(name="Bob's Project",manager=bob,description="Belongs to Joe", status="None", phase="None")
		joeTask = ProjectTask.objects.create(summary="Joe's Task",creator=joe,description="Joe's")
		bobTask = ProjectTask.objects.create(summary="Bob's Task",creator=bob,description="Bob's")


	def test_create_task( self ):

		tdata = {}
		tdata['summary'] = "My Task"
		tdata['description'] = "Just Mine"

		c = Client()
		response = c.post('/projects/addtask/', tdata)

		self.assertEqual( ProjectTask.objects.filter(summary="Just Mine").count(), 0 )

		c.login( username='joe', password='pass')

		t = ProjectTask.objects.get(id=1)

		response = c.post('/projects/addtask/', tdata)
		self.assertEqual( ProjectTask.objects.filter(summary="My Task").count(), 1 )

		t = ProjectTask.objects.get( summary="My Task" )

		self.assertEqual( t.summary, "My Task" )
		self.assertEqual( t.description, "Just Mine" )

	def test_edit_task( self ):

		tdata = {}
		tdata['summary'] = "My Task"
		tdata['description'] = "Just Mine"

		c = Client()
		response = c.post('/projects/task/edit/1/', tdata )

		t = ProjectTask.objects.get( id=1 )

		self.assertEqual( t.summary, "Joe's Task" )

		c.login( username='joe', password='pass' )

		response = c.post('/projects/task/edit/1/', tdata )

		t = ProjectTask.objects.get( id=1 )

		self.assertEqual( t.summary, "My Task" )


	def test_create_task_and_assign( self ):

		tdata = {}
		tdata['summary'] = "My Task"
		tdata['description'] = "Just Mine"

		c = Client()
		c.login( username='joe', password='pass')

		t = ProjectTask.objects.get(id=1)

		response = c.post('/projects/addtask/1/', tdata)
		self.assertEqual( ProjectTask.objects.filter(summary="My Task").count(), 1 )

		t = ProjectTask.objects.get( summary="My Task" )

		self.assertEqual( t.summary, "My Task" )
		self.assertEqual( t.description, "Just Mine" )

		p = Project.objects.get( id=1 )

		self.assertTrue( p in t.openOn.all() )

	def test_user_task_show( self ):

		c = Client()
		c.login( username='joe', password='pass')

		bobTask = ProjectTask.objects.get(id=2)
		joeTask = ProjectTask.objects.get(id=1)

		joe = User.objects.get( username='joe' )
		bobProject = Project.objects.get( id=2 )

		bobTask.assigned.add( joe )
		bobTask.openOn.add( bobProject )
		bobTask.save()

		response = c.get('/projects/todo/')

		self.assertTrue( 'tasks' in response.context )
		self.assertTrue( bobTask in response.context['tasks'] )

		response = c.get('/projects/usertasks/')

		self.assertTrue( 'tasks' in response.context )
		self.assertTrue( joeTask in response.context['tasks'] )

	def test_wip_toggle( self ):
		c = Client()
		c.login( username='joe', password='pass')

		response = c.get('/projects/task/inprogress/1/')

		joeProject = ProjectTask.objects.get(id=1)

		self.assertTrue( joeProject.inProgress )

		response = c.get('/projects/task/inprogress/1/')

		joeProject = ProjectTask.objects.get(id=1)

		self.assertFalse( joeProject.inProgress )






class TagActions(TestCase):

	def setUp(self):
		joe= get_user_model().objects.create_user(username='joe', email=None, password='pass')
		bob= get_user_model().objects.create_user(username="bob", first_name="Bob", last_name="Herp", email="bob@joe.joe", password="pass")
		joeProject=Project.objects.create(name="Joe's Project",manager=joe,description="Belongs to Joe", status="None", phase="None")
		bobProject=Project.objects.create(name="Bob's Project",manager=bob,description="Belongs to Joe", status="None", phase="None")
		joeTask = ProjectTask.objects.create(summary="Joe's Task",creator=joe,description="Joe's")
		bobTask = ProjectTask.objects.create(summary="Bob's Task",creator=bob,description="Bob's")

	def test_create_private_tag(self):
		c = Client()
		c.login( username='joe', password='pass' )

		tagData = {}
		tagData['name'] = 'joetag'
		tagData['description'] = "Joe's Tag"

		response = c.post('/projects/newtag/', tagData)

		tag = Tag.objects.filter( name='joetag' )

		self.assertEqual( tag.count(), 1 )
		self.assertFalse( tag[0].public )

	def test_create_public_tag( self ):
		c = Client()
		c.login( username='joe', password='pass' )

		tagData = {}
		tagData['name'] = 'joetag'
		tagData['description'] = "Joe's Tag"
		tagData['public'] = True

		response = c.post('/projects/newtag/', tagData)

		tag = Tag.objects.filter( name='joetag' )

		self.assertEqual( tag.count(), 1 )
		self.assertTrue( tag[0].public )









class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)
