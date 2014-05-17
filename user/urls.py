from django.conf.urls import patterns, include, url

urlpatterns = patterns('',

  url(r'^user/register/$',        'user.views.register_user'),
  url(r'^user/login/$',             'user.views.login_user'),
  url(r'^user/auth/$',             'user.views.auth_user'),
  url(r'^user/welcome/$',      'project.views.project_welcome'),
  url(r'^user/logout/$',          'user.views.logout'),
  url(r'^accounts/login/$',     'user.views.login_user'),
  url(r'^user/profile/(?P<username>[a-zA-Z0-9_.-]+)/$',
                                            'user.views.view_profile'),
  url(r'^profile/(?P<username>[a-zA-Z0-9_.-]+)/$',
                                            'user.views.view_profile'),
  url(r'^u/(?P<username>[a-zA-Z0-9_.-]+)/$',
                                            'user.views.view_profile'),
  url(r'^user/edit/$',              'user.views.edit_profile'),
  url(r'^user/password/$',    'user.views.change_password'),
  url(r'^user/settings/$', 'user.views.settings_dashboard'),

)
