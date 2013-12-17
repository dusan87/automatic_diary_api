from django.conf.urls import patterns, include, url
from rest_framework import routers

# Uncomment the next two lines to enable the admin:
#from django.contrib import admin
#admin.autodiscover()



#router.register(r'android_auth', UserHandler)

urlpatterns = patterns('api.views',
    # Examples:
    # url(r'^$', 'automatic_diary_server.views.home', name='home'),
    # url(r'^automatic_diary_server/', include('automatic_diary_server.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    #url(r'^admin/', include(admin.site.urls)),
    url(r'^create_user/$', 'create_user'),
    url(r'^login_user/$', 'login_user'),
    url(r'^check_user/$', 'check_user')
)
