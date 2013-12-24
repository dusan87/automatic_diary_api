from django.conf.urls import patterns, include, url
from rest_framework import routers
import settings
# Uncomment the next two lines to enable the admin:
#from django.contrib import admin
#admin.autodiscover()



#router.register(r'android_auth', UserHandler)

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'automatic_diary_server.views.home', name='home'),
    # url(r'^automatic_diary_server/', include('automatic_diary_server.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    #url(r'^admin/', include(admin.site.urls)),
    url(r'^create_user/$', 'api.views.create_user'),
    url(r'^login_user/$', 'api.views.login_user'),
    url(r'^check_user/$', 'api.views.check_user'),
    url(r'^all_users/$', 'api.views.all_users'),
    (r'^media/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.MEDIA_ROOT})
)
