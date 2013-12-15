from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'webtrack.views.home', name='home'),
    # url(r'^webtrack/', include('webtrack.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),

    # URLs for the user application
    url(r'^$', 'user.views.welcome'),
    url(r'^user/register/$', 'user.views.register_user'),
    url(r'^user/login/$', 'user.views.login_user'),
    url(r'^user/auth/$', 'user.views.auth_user'),
    url(r'^user/welcome/$', 'user.views.welcome'),
    url(r'^user/logout/$', 'user.views.logout'),
    url(r'^accounts/login/$', 'user.views.login_user'),

    # URLs for the project application
    url(r'^projects/welcome/$', 'project.views.project_welcome'),
    url(r'^projects/$', 'project.views.list_projects'),
    url(r'^projects/create/$', 'project.views.create_project'),
    url(r'^projects/view/(?P<proj_id>\d+)/$', 'project.views.view_project'),
    url(r'^projects/edit/(?P<proj_id>\d+)/$', 'project.views.edit_project'),
    url(r'^projects/addmember/(?P<proj_id>\d+)/$', 'project.views.add_member'),
    url(r'^projects/removemember/(?P<proj_id>\d+)/(?P<user_id>\d+)/$', 'project.views.remove_member'),
    url(r'^projects/addwork/(?P<proj_id>\d+)/$', 'project.views.add_worklog'),
    url(r'^projects/work/view/(?P<log_id>\d+)/$', 'project.views.view_worklog'),
    url(r'^projects/work/edit/(?P<log_id>\d+)/$', 'project.views.edit_worklog'),
    url(r'^projects/work/viewall/(?P<proj_id>\d+)/$', 'project.views.view_all_work'),
    url(r'^projects/stats/lines/$', 'project.views.line_stats'),
    url(r'^projects/addtask/(?P<proj_id>\d+)/$', 'project.views.add_task'),
    url(r'^projects/addtask/$', 'project.views.add_task'),
    url(r'^projects/task/view/(?P<task_id>\d+)/$', 'project.views.view_task'),
    url(r'^projects/task/edit/(?P<task_id>\d+)/$', 'project.views.edit_task'),
    url(r'^projects/task/viewall/(?P<proj_id>\d+)/$', 'project.views.view_all_task'),
    url(r'^projects/task/addmember/(?P<task_id>\d+)/$', 'project.views.add_task_member'),
    url(r'^projects/task/removemember/(?P<task_id>\d+)/(?P<user_id>\d+)/$', 'project.views.remove_task_member'),
    url(r'^projects/(?P<project_id>\d+)/closetask/(?P<task_id>\d+)/$', 'project.views.close_task_in_project'),
    url(r'^projects/(?P<project_id>\d+)/opentask/(?P<task_id>\d+)/$', 'project.views.open_task_in_project'),
    url(r'^projects/usertasks/$', 'project.views.user_all_tasks'),
    url(r'^projects/addtotask/(?P<task_id>\d+)/$', 'project.views.add_existing_task_to_project'),
    url(r'^projects/addtotask/(?P<task_id>\d+)/(?P<project_id>\d+)/$', 'project.views.add_existing_task_to_project'),
    url(r'^projects/task/delete/(?P<task_id>\d+)/$', 'project.views.delete_task'),

    url(r'^projects/todo/', 'project.views.my_todo'),


)
