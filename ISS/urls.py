"""ISS URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from ISS import views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url('^thread/(?P<thread_id>\d+)/?$', views.thread, name='thread'),
    url('^thread/(?P<thread_id>\d+)/new-reply/?$', views.NewReply.as_view(),
        name='new-reply'),
    url('^forum/(?P<forum_id>\d+)/new-thread$', views.NewThread.as_view(),
        name='new-thread'),
    url('^forum/(?P<forum_id>\d+)/?$', views.thread_index, name='thread-index'),
    url('^latest-threads/?$', views.latest_threads, name='latest-threads'),
    url(r'^/?$', views.forum_index, name='forum-index'), 
    url(r'^register/$', views.RegisterUser.as_view(), name='register'),
    url(r'^login/$', views.LoginUser.as_view(), name='login'),
    url(r'^logout/$', views.LogoutUser.as_view(), name='logout'),
    url(r'^user/(?P<user_id>\d+)/?$', views.user_profile, name='user-profile'),
    url(r'^user/(?P<user_id>\d+)/posts/?$', views.posts_by_user,
        name='posts-by-user'),
    url(r'^post/(?P<post_id>\d+)/get-quote$', views.GetQuote.as_view(),
        name='get-quote'),
]
