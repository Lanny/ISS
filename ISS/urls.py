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
from django.contrib.sitemaps.views import sitemap
from django.views.generic import TemplateView

from ISS import views, utils
from ISS.sitemaps import iss_sitemaps

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^houston/', include('Houston.urls')),

    url(r'^humans.txt$', views.misc.humans, name='humans'),
    url(r'^robots.txt$', views.misc.robots, name='robots'),
    url(r'^sitemap.xml$', sitemap, {'sitemaps': iss_sitemaps}, name='sitemap'),

    url(r'^smilies.css', views.misc.smilies_css, name='smilies-css'),
    url(r'^smiley-reference',
        TemplateView.as_view(template_name="smilies_reference.html"),
        name='smilies-reference'),

    url(r'^thread/(?P<thread_id>\d+)/?$',
        views.forum.thread,
        name='thread'),
    url(r'^thread/(?P<thread_id>\d+)/action$',
        views.forum.ThreadActions.as_view(),
        name='thread-action'),
    url(r'^post/(?P<post_id>\d+)/?$',
        views.forum.redirect_to_post,
        name='post'),
    url(r'^thread/(?P<thread_id>\d+)/new-reply/?$',
        views.forum.NewReply.as_view(),
        name='new-reply'),
    url(r'^thread/(?P<thread_id>\d+)/unsubscribe$',
        views.forum.UnsubscribeFromThread.as_view(),
        name='unsubscribe'),
    url(r'^preview-(?P<action>edit|thread|post|compose-pm)$',
        views.forum.PreviewPost.as_view(),
        name='preview-post'),

    url(r'^forum/(?P<forum_id>\d+)/new-thread$',
        views.forum.NewThread.as_view(),
        name='new-thread'),
    url(r'^forum/(?P<forum_id>\d+)/?$',
        views.forum.thread_index,
        name='thread-index'),

    url('^latest-threads/?$',
        views.forum.latest_threads,
        name='latest-threads'),
    url('^latest-threads/preferences?$',
        views.forum.UpdateLatestThreadsPreferences.as_view(),
        name='latest-threads-preferences'),
    url(r'^$',
        views.forum.forum_index,
        name='forum-index'),
    url(r'^invite/generate$',
        views.user.GenerateInvite.as_view(),
        name='generate-invite'),
    url(r'^invite/complete$',
        views.user.view_generated_invite,
        name='view-generated-invite'),
    url(r'^register/$',
        views.user.RegisterUser.as_view(),
        name='register'),
    url(r'^register/invite$',
        views.user.RegisterUserWithCode.as_view(),
        name='register-with-code'),
    url(r'^register/verify-email',
        views.user.VerifyEmail.as_view(),
        name='verify-email'),
    url(r'^recovery/initiate$',
        views.user.InitiatePasswordRecovery.as_view(),
        name='recovery-initiate'),
    url(r'^recovery/reset$',
        views.user.ExecutePasswordRecovery.as_view(),
        name='recovery-reset'),
    url(r'^login/$',
        views.forum.LoginUser.as_view(),
        name='login'),
    url(r'^logout/$',
        views.forum.LogoutUser.as_view(),
        name='logout'),

    url(r'^user/(?P<user_id>\d+)/?$',
        views.user.UserProfile.as_view(),
        name='user-profile'),
    url(r'^user/(?P<user_id>\d+)/posts/?$',
        views.forum.posts_by_user,
        name='posts-by-user'),
    url(r'^user/(?P<user_id>\d+)/threads/?$',
        views.forum.threads_by_user,
        name='threads-by-user'),
    url(r'^user/(?P<user_id>\d+)/thankedposts/?$',
        views.forum.thanked_posts,
        name='thanked-posts'),
    url(r'^user/(?P<user_id>\d+)/poststhanked/?$',
        views.forum.posts_thanked,
        name='posts-thanked'),
    url(r'^user/(?P<user_id>\d+)/ban$',
        views.forum.BanPoster.as_view(),
        name='ban-poster'),

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
    url(r'^post/(?P<post_id>\d+)/report$',
        views.forum.ReportPost.as_view(),
        name='report-post'),

    url(r'^help/bbcode',
        TemplateView.as_view(template_name="bbcode_help.html"),
        name='bbcode-help'),

    url(r'^misc/echo',
        views.misc.EchoForm.as_view(),
        name='echo'),
    url('^search$',
        views.forum.search,
        name='search'),
    url('^usercp$',
        views.forum.usercp,
        name='usercp'),
    url('^usercp/mark-read$',
        views.forum.MarkSubsriptionsRead.as_view(),
        name='read-subscriptions'),
    url('^auto-anonymize$',
        views.forum.AutoAnonymize.as_view(),
        name='auto-anonymize'),
    url(r'^members$',
        views.user.UserIndex.as_view(),
        name='members'),
    url(r'^find-user$',
        views.user.FindUser.as_view(),
        name='find-user'),

    url('^page/(?P<page_id>.*)',
        views.misc.view_static_page,
        name="static-page"),

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
        name='read-pm'),
    url(r'^pms/inbox/action$',
        views.private_messages.PrivateMessageActions.as_view(),
        name='pms-action'),

    url(r'^thread/(?P<thread_id>\d+)/create-poll$',
        views.polls.CreatePoll.as_view(),
        name='create-poll'),

    url(r'^api/users/search$',
        views.user.user_fuzzy_search,
        name='api-user-serach'),
    url(r'^api/bbcode/render$',
        views.forum.RenderBBCode.as_view(),
        name='api-render-bbcode')
]

# Install urls for extensions.
for ext in utils.get_config('extensions'):
    base_path = utils.get_ext_config(ext, 'base_path')

    if base_path:
        urlpatterns.append(url(base_path, include(ext + '.urls')))

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
