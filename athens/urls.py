from django.conf.urls import patterns, include, url
from democracy.views import login_view
from django.contrib import admin
from django.conf import settings
admin.autodiscover()
from dajaxice.core import dajaxice_autodiscover, dajaxice_config
dajaxice_autodiscover()
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from wiki.urls import get_pattern as get_wiki_pattern
from django_notify.urls import get_pattern as get_notify_pattern
from django.views.generic import RedirectView




urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'athens.views.home', name='home'),
    # url(r'^athens/', include('athens.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
     url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
     (r'^democracy/favicon\.ico$', RedirectView.as_view(url='media/mocks/favicon.ico')),

    # Uncomment the next line to enable the admin:
     url(r'^admin/', include(admin.site.urls)),


     url(r'^democracy/', include('democracy.urls')),
     url(r'^democracy/msg/', include('threaded_messages.urls')),
     url(r'^notification/', include('notification.urls')),
     url(r'^accounts/login/$', 'django.contrib.auth.views.login'),

     url(dajaxice_config.dajaxice_url, include('dajaxice.urls')),
    (r'^notify/', get_notify_pattern()),
    (r'', get_wiki_pattern()),
    (r'^avatar/', include('avatar.urls')),
    (r'^media/(?P<path>.*)$', 'django.views.static.serve',{'document_root': settings.MEDIA_ROOT}),
     

)
urlpatterns += staticfiles_urlpatterns()
