from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url(r'^$', 'datacollection.views.home', name='home'),
    url(r'^register/$', 'datacollection.views.register'),
    url(r'^login/$', 'datacollection.views.system_login'),
    url(r'^logout/$', 'datacollection.views.system_logout'),
    url(r'^facebook_player/$', 'datacollection.views.facebook_player'),
    url(r'^linkedin_player/$', 'datacollection.views.linkedin_player'),
    url(r'^lastfm_player/$', 'datacollection.views.lastfm_player'),
    url(r'^twitter_player/$', 'datacollection.views.twitter_player'),
    url(r'^gplus_player/$', 'datacollection.views.gplus_player'),
    url(r'^flickr_player/$', 'datacollection.views.flickr_player'),
    url(r'^refresh/$', 'datacollection.views.refresh'),
)
