from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
  url(r'^new/(?P<proj_id>\d+)/$',
                                'worklogs.views.add_worklog'),
  url(r'^(?P<log_id>\d+)/$',
                                  'worklogs.views.view_worklog'),
  url(r'^edit/(?P<log_id>\d+)/$',
                                  'worklogs.views.edit_worklog'),
  url(r'^viewall/(?P<proj_id>\d+)/$',
                                  'worklogs.views.view_all_work'),
  url(r'^$', 'worklogs.views.list_worklogs'),

  url(r'^settings/$', 'worklogs.views.edit_settings'),

)
