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

class ProjectViewUpdate(TestCase):

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




class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)
