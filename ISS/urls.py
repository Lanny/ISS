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
from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin

from ISS import views

urlpatterns = [
    url(r'^admin/', admin.site.urls),

    url('^thread/(?P<thread_id>\d+)/?$',
        views.forum.thread,
        name='thread'),
    url('^thread/(?P<thread_id>\d+)/new-reply/?$',
        views.forum.NewReply.as_view(),
        name='new-reply'),
    url('^forum/(?P<forum_id>\d+)/new-thread$',
        views.forum.NewThread.as_view(),
        name='new-thread'),
    url('^forum/(?P<forum_id>\d+)/?$',
        views.forum.thread_index,
        name='thread-index'),
    url('^latest-threads/?$',
        views.forum.latest_threads,
        name='latest-threads'),
    url(r'^/?$',
        views.forum.forum_index,
        name='forum-index'), 
    url(r'^register/$',
        views.forum.RegisterUser.as_view(),
        name='register'),
    url(r'^login/$',
        views.forum.LoginUser.as_view(),
        name='login'),
    url(r'^logout/$',
        views.forum.LogoutUser.as_view(),
        name='logout'),
    url(r'^user/(?P<user_id>\d+)/?$',
        views.forum.UserProfile.as_view(),
        name='user-profile'),
    url(r'^user/(?P<user_id>\d+)/posts/?$',
        views.forum.posts_by_user,
        name='posts-by-user'),
    url(r'^user/(?P<user_id>\d+)/thankedposts/?$',
        views.forum.thanked_posts,
        name='thanked-posts'),
    url(r'^post/(?P<post_id>\d+)/get-quote$', 
        views.forum.GetQuote.as_view(),
        name='get-quote'),
    url(r'^post/(?P<post_id>\d+)/thank-post$', 
        views.forum.ThankPost.as_view(),
        name='thank-post'),
    url(r'^post/(?P<post_id>\d+)/unthank-post$',
        views.forum.UnthankPost.as_view(),
        name='unthank-post'),
    url(r'^post/(?P<post_id>\d+)/edit$',
        views.forum.EditPost.as_view(),
        name='edit-post'),
    url('^search$',
        views.forum.search,
        name='search'),
    url('^usercp$',
        views.forum.usercp,
        name='usercp'),

    url('^embed/bandcamp',
        views.forum.get_bc_embed_code,
        name='embed-bandcamp'),

    url(r'^admin/user/(?P<user_id>\d+)/assume-identity$',
        views.forum.assume_identity,
        name='assume-identity'),
    url(r'^admin/user/(?P<poster_id>\d+)/spam-can$',
        views.forum.SpamCanUser.as_view(),
        name='spam-can-user'),

    url(r'^pms/inbox$',
        views.private_messages.inbox,
        name='inbox'),
    url(r'^pms/sent$',
        views.private_messages.sent,
        name='sent-pms'),
    url(r'^pms/compose$',
        views.private_messages.NewPrivateMessage.as_view(),
        name='compose-pm'),
    url(r'^pms/read/(?P<pm_id>\d+)$',
        views.private_messages.read_pm,
        name='read-pm')
]


urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]

