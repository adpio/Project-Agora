from django.conf.urls import patterns, url, include
from democracy import views
from django.contrib.auth.views import login, logout

urlpatterns = patterns('',
	url(r'^$', views.index, name='index'),
    url(r'^profile/$', views.profile, name='profile'),
    (r'^profiles/', include('profiles.urls')),

    #creators
    url(r'^login/$', views.login_view, name='login_view'),
    url(r'^createorg/$', views.form_org, name='from_org'),
    url(r'^createuser/$', views.form_user, name='form_user'),

    #specific creators
    url(r'^(?P<org_id>\d+)/createbody/$', views.form_body, name='form_body'),
    url(r'^(?P<org_id>\d+)/body/(?P<body_id>\d+)/createtodo$', views.form_todo, name='form_todo' ),
    url(r'^(?P<org_id>\d+)/associate/$', views.associate, name='associate'),
    url(r'^(?P<org_id>\d+)/body/(?P<body_id>\d+)/candidate$', views.add_candidate, name='candidate'),
    url(r'^(?P<org_id>\d+)/body/(?P<body_id>\d+)/admission_detail$', views.admission_detail, name='admission_detail'),
    url(r'^(?P<org_id>\d+)/body/(?P<body_id>\d+)/create_election$', views.create_election, name='create_election'),
    url(r'^(?P<org_id>\d+)/body/(?P<body_id>\d+)/election/(?P<election_id>\d+)/start_election$', views.start_election, name='start_election'),

    #displayers
    url(r'^(?P<org_id>\d+)/$', views.org_detail, name='org_detail'),
    url(r'^(?P<org_id>\d+)/body/(?P<body_id>\d+)/$', views.body_detail, name='body_detail' ),
    url(r'^(?P<org_id>\d+)/body/(?P<body_id>\d+)/todo/(?P<todo_id>\d+)/$', views.todo_detail, name='todo_detail'),
    url(r'^(?P<org_id>\d+)/body/(?P<body_id>\d+)/todo/(?P<todo_id>\d+)/review$', views.review_detail, name='review_detail'),
    url(r'^(?P<org_id>\d+)/body/(?P<body_id>\d+)/election/(?P<election_id>\d+)/$', views.election_detail, name='election_detail'),

    )

