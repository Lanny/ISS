from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, re_path, path
from django.views.generic import TemplateView

from ISS import views, utils
from ISS.sitemaps import iss_sitemaps

urlpatterns = [
    re_path(r'^admin/', admin.site.urls),

    re_path(r'^humans.txt$', views.misc.humans, name='humans'),
    re_path(r'^robots.txt$', views.misc.robots, name='robots'),
    re_path(r'^sitemap.xml$', sitemap, {'sitemaps': iss_sitemaps}, name='sitemap'),

    re_path(r'^smilies.css', views.misc.smilies_css, name='smilies-css'),
    re_path(r'^smiley-reference',
        TemplateView.as_view(template_name="smilies_reference.html"),
        name='smilies-reference'),

    re_path(r'^thread/(?P<thread_id>\d+)/?$',
        views.forum.thread,
        name='thread'),
    re_path(r'^thread/(?P<thread_id>\d+)/action$',
        views.forum.ThreadActions.as_view(),
        name='thread-action'),
    re_path(r'^post/(?P<post_id>\d+)/?$',
        views.forum.redirect_to_post,
        name='post'),
    re_path(r'^thread/(?P<thread_id>\d+)/new-reply/?$',
        views.forum.NewReply.as_view(),
        name='new-reply'),
    re_path(r'^thread/(?P<thread_id>\d+)/unsubscribe$',
        views.forum.UnsubscribeFromThread.as_view(),
        name='unsubscribe'),
    re_path(r'^preview-(?P<action>edit|thread|post|compose-pm)$',
        views.forum.PreviewPost.as_view(),
        name='preview-post'),

    re_path(r'^forum/(?P<forum_id>\d+)/new-thread$',
        views.forum.NewThread.as_view(),
        name='new-thread'),
    re_path(r'^forum/(?P<forum_id>\d+)/?$',
        views.forum.thread_index,
        name='thread-index'),

    re_path('^latest-threads/?$',
        views.forum.latest_threads,
        name='latest-threads'),
    re_path('^latest-threads/preferences?$',
        views.forum.UpdateLatestThreadsPreferences.as_view(),
        name='latest-threads-preferences'),
    re_path(r'^$',
        views.forum.forum_index,
        name='forum-index'),
    re_path(r'^invite/generate$',
        views.user.GenerateInvite.as_view(),
        name='generate-invite'),
    re_path(r'^invite/complete$',
        views.user.view_generated_invite,
        name='view-generated-invite'),
    re_path(r'^register/$',
        views.user.RegisterUser.as_view(),
        name='register'),
    re_path(r'^register/invite$',
        views.user.RegisterUserWithCode.as_view(),
        name='register-with-code'),
    re_path(r'^register/verify-email',
        views.user.VerifyEmail.as_view(),
        name='verify-email'),
    re_path(r'^recovery/initiate$',
        views.user.InitiatePasswordRecovery.as_view(),
        name='recovery-initiate'),
    re_path(r'^recovery/reset$',
        views.user.ExecutePasswordRecovery.as_view(),
        name='recovery-reset'),
    re_path(r'^login/$',
        views.forum.LoginUser.as_view(),
        name='login'),
    re_path(r'^logout/$',
        views.forum.LogoutUser.as_view(),
        name='logout'),

    re_path(r'^user/(?P<user_id>\d+)/?$',
        views.user.UserProfile.as_view(),
        name='user-profile'),
    re_path(r'^user/(?P<user_id>\d+)/posts/?$',
        views.forum.posts_by_user,
        name='posts-by-user'),
    re_path(r'^user/(?P<user_id>\d+)/threads/?$',
        views.forum.threads_by_user,
        name='threads-by-user'),
    re_path(r'^user/(?P<user_id>\d+)/thankedposts/?$',
        views.forum.thanked_posts,
        name='thanked-posts'),
    re_path(r'^user/(?P<user_id>\d+)/poststhanked/?$',
        views.forum.posts_thanked,
        name='posts-thanked'),
    re_path(r'^user/(?P<user_id>\d+)/ban$',
        views.forum.BanPoster.as_view(),
        name='ban-poster'),

    re_path(r'^post/(?P<post_id>\d+)/get-quote$',
        views.forum.GetQuote.as_view(),
        name='get-quote'),
    re_path(r'^post/(?P<post_id>\d+)/thank-post$',
        views.forum.ThankPost.as_view(),
        name='thank-post'),
    re_path(r'^post/(?P<post_id>\d+)/unthank-post$',
        views.forum.UnthankPost.as_view(),
        name='unthank-post'),
    re_path(r'^post/(?P<post_id>\d+)/edit$',
        views.forum.EditPost.as_view(),
        name='edit-post'),
    re_path(r'^post/(?P<post_id>\d+)/report$',
        views.forum.ReportPost.as_view(),
        name='report-post'),

    re_path(r'^help/bbcode',
        TemplateView.as_view(template_name="bbcode_help.html"),
        name='bbcode-help'),

    re_path(r'^misc/echo',
        views.misc.EchoForm.as_view(),
        name='echo'),
    re_path('^search$',
        views.forum.search,
        name='search'),
    re_path('^usercp$',
        views.forum.usercp,
        name='usercp'),
    re_path('^usercp/mark-read$',
        views.forum.MarkSubsriptionsRead.as_view(),
        name='read-subscriptions'),
    re_path('^auto-anonymize$',
        views.forum.AutoAnonymize.as_view(),
        name='auto-anonymize'),
    re_path(r'^members$',
        views.user.UserIndex.as_view(),
        name='members'),
    re_path(r'^find-user$',
        views.user.FindUser.as_view(),
        name='find-user'),

    re_path('^page/(?P<page_id>.*)',
        views.misc.view_static_page,
        name="static-page"),

    re_path('^embed/bandcamp',
        views.forum.get_bc_embed_code,
        name='embed-bandcamp'),

    re_path(r'^iss-admin/user/(?P<user_id>\d+)/assume-identity$',
        views.forum.assume_identity,
        name='assume-identity'),
    re_path(r'^iss-admin/user/(?P<poster_id>\d+)/spam-can$',
        views.forum.SpamCanUser.as_view(),
        name='spam-can-user'),

    re_path(r'^pms/inbox$',
        views.private_messages.inbox,
        name='inbox'),
    re_path(r'^pms/sent$',
        views.private_messages.sent,
        name='sent-pms'),
    re_path(r'^pms/compose$',
        views.private_messages.NewPrivateMessage.as_view(),
        name='compose-pm'),
    re_path(r'^pms/read/(?P<pm_id>\d+)$',
        views.private_messages.read_pm,
        name='read-pm'),
    re_path(r'^pms/inbox/action$',
        views.private_messages.PrivateMessageActions.as_view(),
        name='pms-action'),

    re_path(r'^thread/(?P<thread_id>\d+)/create-poll$',
        views.polls.CreatePoll.as_view(),
        name='create-poll'),
    re_path(r'^polls/(?P<poll_id>\d+)/vote$',
        views.polls.CastVote.as_view(),
        name='vote-on-poll'),

    re_path(r'^api/users/search$',
        views.user.user_fuzzy_search,
        name='api-user-serach'),
    re_path(r'^api/bbcode/render$',
        views.forum.RenderBBCode.as_view(),
        name='api-render-bbcode')
]

# Install urls for extensions.
for ext in utils.get_config('extensions'):
    base_path = utils.get_ext_config(ext, 'base_path')

    if base_path:
        urlpatterns.append(re_path(base_path, include(ext + '.urls')))

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    try:
        import debug_toolbar

        urlpatterns += [
            path('__debug__/', include(debug_toolbar.urls)),
        ]
    except:
        print('Unable to import debug_toolbar but settings.DEBUG was true!')
