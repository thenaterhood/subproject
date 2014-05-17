from django.conf.urls import patterns, include, url

urlpatterns = patterns('',

  url(r'^new/$',            'tagging.views.add_tag'),
  url(r'^view/(?P<tag_id>\d+)/$',
                                  'tagging.views.view_tag'),
  url(r'^(?P<tag_id>\d+)/$',
                                  'tagging.views.view_tag'),
  url(r'^edit/(?P<tag_id>\d+)/$',
                                  'tagging.views.add_tag' ),
  url(r'^delete/(?P<tag_id>\d+)/$',
                                  'tagging.views.delete_tag' ),
  url(r'^adduser/(?P<tag_id>\d+)/$',
                                  'tagging.views.toggle_tag_user' ),
  url(r'^addviewer/(?P<tag_id>\d+)/$',
                                  'tagging.views.toggle_tag_viewer' ),
  url(r'^(?P<tag_id>\d+)/revokeuser/(?P<user_id>\d+)/$',
                                  'tagging.views.toggle_tag_user' ),
  url(r'^(?P<tag_id>\d+)/revokeviewer/(?P<user_id>\d+)/$',
                                  'tagging.views.toggle_tag_viewer' ),
  url(r'^$',                   'tagging.views.list_tags'),

)
