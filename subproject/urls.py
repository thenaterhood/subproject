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
    url(r'^$',                      'project.views.project_welcome'),
    url(r'^user/register/$',        'user.views.register_user'),
    url(r'^user/login/$',           'user.views.login_user'),
    url(r'^user/auth/$',            'user.views.auth_user'),
    url(r'^user/welcome/$',         'project.views.project_welcome'),
    url(r'^user/logout/$',          'user.views.logout'),
    url(r'^accounts/login/$',       'user.views.login_user'),
    url(r'^user/profile/(?P<username>[a-zA-Z0-9_.-]+)/$',
                                    'user.views.view_profile'),
    url(r'^profile/(?P<username>[a-zA-Z0-9_.-]+)/$',
                                    'user.views.view_profile'),
    url(r'^u/(?P<username>[a-zA-Z0-9_.-]+)/$',
                                    'user.views.view_profile'),
    url(r'^user/edit/$',            'user.views.edit_profile'),
    url(r'^user/password/$',        'user.views.change_password'),

    # URLs for the project application
    url(r'^projects/welcome/$',     'project.views.project_welcome'),
    url(r'^projects/$',             'project.views.list_projects'),

    # Project creation and management
    url(r'^projects/create/$',      'project.views.create_project'),
    url(r'^projects/view/(?P<proj_id>\d+)/$',
                                    'project.views.view_project'),
    url(r'^u/(?P<username>[a-zA-Z0-9_.-]+)/projects/(?P<projectname>[a-zA-Z0-9_\s.-]+)/$',
                                    'project.views.view_project'),
    url(r'^u/(?P<user>[a-zA-Z0-9_.-]+)/projects/$',
                                    'project.views.list_projects'),
    url(r'^projects/edit/(?P<pid>\d+)/$',
                                    'project.views.create_project'),
    url(r'^projects/newsub/(?P<parent>\d+)/$',
                                    'project.views.create_project'),
    url(r'^projects/newsub/$',      'project.views.create_project'),

    # Subproject management
    url(r'^projects/totop/(?P<project_id>\d+)/$',
                                    'project.views.project_to_top'),
    url(r'^projects/children/(?P<project_id>\d+)/$',
                                    'project.views.show_children'),
    url(r'^projects/parents/(?P<project_id>\d+)/$',
                                    'project.views.show_parents'),
    url(r'^projects/(?P<parent_id>\d+)/assignchild/$',
                                    'project.views.assign_child'),
    url(r'^projects/(?P<parent_id>\d+)/assignchild/(?P<child_id>\d+)/$',
                                    'project.views.assign_child'),

    # Project member management
    url(r'^u/(?P<user>[a-zA-Z0-9_.-]+)/tasks/$',
                                    'tasks.views.all_tasks'),
    url(r'^projects/addmember/(?P<proj_id>\d+)/$',
                                    'project.views.add_member'),
    url(r'^projects/removemember/(?P<proj_id>\d+)/(?P<user_id>\d+)/$',
                                    'project.views.remove_member'),
    url(r'^projects/addwork/(?P<proj_id>\d+)/$',
                                    'worklogs.views.add_worklog'),

    # Task creation and management
    url(r'^projects/addtask/(?P<proj_id>\d+)/$',
                                    'tasks.views.add_task'),
    url(r'^projects/addtask/$',     'tasks.views.add_task'),
    url(r'^projects/task/view/(?P<task_id>\d+)/$',
                                    'tasks.views.view_task'),
    url(r'^projects/task/edit/(?P<task_id>\d+)/$',
                                    'tasks.views.edit_task'),
    url(r'^projects/task/viewall/(?P<proj_id>\d+)/$',
                                    'project.views.view_all_task'),
    url(r'^projects/task/addmember/(?P<task_id>\d+)/$',
                                    'tasks.views.add_task_member'),
    url(r'^projects/task/removemember/(?P<task_id>\d+)/(?P<user_id>\d+)/$',
                                    'tasks.views.remove_task_member'),
    url(r'^projects/task/delete/(?P<task_id>\d+)/$',
                                    'tasks.views.delete_task'),
    url(r'^projects/task/tosubproject/(?P<task_id>\d+)/$',
                                    'project.views.convert_task_to_subproject'),
    url(r'^projects/toggle/(?P<project_id>\d+)/$',
                                    'project.views.toggle_project'),


    # Project task management
    url(r'^projects/task/close/(?P<task_id>\d+)/$',
                                    'project.views.toggle_project_task_status'),
    url(r'^projects/task/open/(?P<task_id>\d+)/$',
                                    'project.views.toggle_project_task_status'),

    url(r'^projects/(?P<project_id>\d+)/unassigntask/(?P<task_id>\d+)/$',
                                    'project.views.unassign_task_from_project'),
    url(r'^projects/task/inprogress/(?P<task_id>\d+)/$',
                                    'tasks.views.task_progress_toggle'),
    url(r'^projects/addtotask/(?P<task_id>\d+)/$',
                                    'project.views.add_existing_task_to_project'),
    url(r'^projects/addtotask/(?P<task_id>\d+)/(?P<project_id>\d+)/$',
                                    'project.views.add_existing_task_to_project'),
    url(r'^projects/(?P<proj_id>\d+)/assigntask/$',
                                    'project.views.assign_task'),
    url(r'^projects/(?P<proj_id>\d+)/assigntask/(?P<task_id>\d+)/$',
                                    'project.views.assign_task'),


    # Work creation and management
    url(r'^projects/work/view/(?P<log_id>\d+)/$',
                                    'worklogs.views.view_worklog'),
    url(r'^projects/work/edit/(?P<log_id>\d+)/$',
                                    'worklogs.views.edit_worklog'),
    url(r'^projects/work/viewall/(?P<proj_id>\d+)/$',
                                    'project.views.view_all_work'),
    url(r'^work/$', 'worklogs.views.list_worklogs'),

    # Workload/Project views
    url(r'^projects/usertasks/$',   'tasks.views.user_all_tasks'),
    url(r'^projects/tree/$',        'project.views.view_tree'),
    url(r'^projects/tree/(?P<project_id>\d+)/$',
                                    'project.views.view_tree'),
    url(r'^projects/outline/$',     'project.views.show_outline'),
    url(r'^projects/browser/$',     'project.views.show_browser'),
    url(r'^projects/browser/(?P<open_project>\d+)/$',
                                    'project.views.show_browser'),
    url(r'^projects/todo/$',        'tasks.views.my_todo'),
    url(r'^projects/todo/(?P<status>[a-zA-Z]+)/$',
                                    'tasks.views.todo_by_status'),
    url(r'^projects/usertasks/(?P<status>[a-zA-Z]+)/$',
                                    'tasks.views.tasks_by_status'),
    url(r'^projects/tasks/all/$',   'tasks.views.all_tasks'),



    # Tag management
    url(r'^projects/newtag/$',      'tagging.views.add_tag'),
    url(r'^projects/tags/(?P<tag_id>\d+)/$',
                                    'tagging.views.view_tag'),
    url(r'^projects/tag/edit/(?P<tag_id>\d+)/$',
                                    'tagging.views.add_tag' ),
    url(r'^projects/tag/delete/(?P<tag_id>\d+)/$',
                                    'tagging.views.delete_tag' ),
    url(r'^projects/tag/adduser/(?P<tag_id>\d+)/$',
                                    'tagging.views.toggle_tag_user' ),
    url(r'^projects/tag/addviewer/(?P<tag_id>\d+)/$',
                                    'tagging.views.toggle_tag_viewer' ),
    url(r'^projects/tag/(?P<tag_id>\d+)/revokeuser/(?P<user_id>\d+)/$',
                                    'tagging.views.toggle_tag_user' ),
    url(r'^projects/tag/(?P<tag_id>\d+)/revokeviewer/(?P<user_id>\d+)/$',
                                    'tagging.views.toggle_tag_viewer' ),
    url(r'^projects/tags/',         'tagging.views.list_tags'),

    # Tag association
    url(r'^projects/(?P<proj_id>\d+)/addtag/$',
                                    'project.views.assign_project_tag' ),
    url(r'^projects/(?P<proj_id>\d+)/addtag/(?P<tag_id>\d+)/$',
                                    'project.views.assign_project_tag' ),

    url(r'^projects/task/(?P<task_id>\d+)/addtag/$',
                                    'tasks.views.assign_task_tag' ),
    url(r'^projects/task/(?P<task_id>\d+)/addtag/(?P<tag_id>\d+)/$',
                                    'tasks.views.assign_task_tag' ),

    url(r'^projects/(?P<project_id>\d+)/untag/(?P<tag_id>\d+)/$',
                                    'project.views.untag_project' ),
    url(r'^projects/task/(?P<task_id>\d+)/untag/(?P<tag_id>\d+)/$',
                                    'tasks.views.untag_task' ),

    url(r'^projects/(?P<project_id>\d+)/addtag/new',
                                    'tagging.views.add_tag'),
    url(r'^projects/task/(?P<task_id>\d+)/addtag/new',
                                    'tagging.views.add_tag'),

    # Filter stuff
    url(r'^projects/addtaskfilter/(?P<tag_id>\d+)/$',
                                    'filters.views.add_task_filter'),
    url(r'^projects/addprojectfilter/(?P<tag_id>\d+)/$',
                                    'filters.views.add_project_filter'),
    url(r'^projects/addtagfilter/(?P<tag_id>\d+)/$',
                                    'filters.views.add_filter'),

    url(r'^projects/rmtaskfilter/(?P<tag_id>\d+)/$',
                                    'filters.views.remove_task_filter'),
    url(r'^projects/rmprojectfilter/(?P<tag_id>\d+)/$',
                                    'filters.views.remove_project_filter'),

    #url(r'^projects/rmtagfilter/(?P<tag_id>\d+)/$', 'project.views.rm_filter'),
    url(r'^projects/resetfilter/$', 'filters.views.reset_filter'),

    url(r'^projects/filter/taskbyproject/(?P<project_id>\d+)/$',
                                    'filters.views.add_task_project_filter'),
    url(r'^projects/filter/tasknotbyproject/(?P<project_id>\d+)/$',
                                    'filters.views.rm_task_project_filter'),


    url(r'^projects/filter/addprojecttag/$',
                                    'filters.views.select_project_filter'),
    url(r'^projects/filter/addprojecttag/(?P<tag_id>\d+)/$',
                                    'filters.views.select_project_filter'),

    url(r'^projects/filter/addtasktag/$',
                                    'filters.views.select_task_filter'),
    url(r'^projects/filter/addtasktag/(?P<tag_id>\d+)/$',
                                    'filters.views.select_task_filter'),

    # Data importing
    url(r'^projects/import/$',      'project.views.show_import_page'),
    url(r'^projects/importcsv/projects/$',
                                    'project.views.import_project_csv'),
    url(r'^projects/importcsv/work/$',
                                    'worklogs.views.import_worklog_csv'),



)
