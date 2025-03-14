from django.contrib import admin

from .models import *

class ForumInline(admin.TabularInline):
    model = Forum
    extra = 0

admin.site.register(AuthPackage)

class BanInline(admin.TabularInline):
    model = Ban
    fk_name = 'subject'
    fields = ('given_by', 'reason', 'end_date',)
    readonly_fields = ('given_by',)
    extra = 0

@admin.register(Poster)
class PosterAdmin(admin.ModelAdmin):
    exclude = ('avatar',)
    inlines = [BanInline]

@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    readonly_fields = ('author',)

class PostSnapshotInline(admin.TabularInline):
    model = PostSnapshot
    fk_name = 'post'
    fields = ('short_content', 'time')
    readonly_fields = ('short_content', 'time')
    extra = 0
    show_change_link = True

    def short_content(self, snap):
        return snap.content[:200]

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('author', 'thread_name', 'short_content')
    readonly_fields = ('author',)
    inlines = (PostSnapshotInline,)

    def thread_name(self, obj):
        return obj.thread.title[:100]

    def short_content(self, obj):
        return obj.content[:200]

    def get_readonly_fields(self, request, obj=None):
        return self.readonly_fields + ('thread', 'author')


@admin.register(Thanks)
class ThanksAdmin(admin.ModelAdmin):
    list_display = ('post', 'thanker', 'thankee', 'given',)
    readonly_fields = ('thanker', 'thankee', 'post')
    

@admin.register(PostSnapshot)
class PostSnapshotAdmin(admin.ModelAdmin):
    list_display = ('post', 'time', 'short_content')
    readonly_fields = ('post', 'obsolesced_by',)

    def short_content(self, obj):
        return obj.content[:200]


@admin.register(PrivateMessage)
class PrivateMessageAdmin(admin.ModelAdmin):
    list_display = ('subject', 'sender', 'receiver', 'created')
    readonly_fields = ('sender','receiver','inbox')

@admin.register(FilterWord)
class FilterWordAdmin(admin.ModelAdmin):
    list_display = ('pattern', 'replacement', 'active')

@admin.register(Ban)
class BanAdmin(admin.ModelAdmin):
    list_display = ('subject', 'reason', 'start_date', 'end_date', 'given_by')
    readonly_fields = ('subject', 'given_by',)

@admin.register(IPBan)
class IPBanAdmin(admin.ModelAdmin):
    list_display = ('on', 'memo')

@admin.register(AccessControlList)
class AccessControlListAdmin(admin.ModelAdmin):
    list_display = ('name', 'allow_by_default')

@admin.register(AccessControlGroup)
class AccessControlListAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(StaticPage)
class StaticPageAdmin(admin.ModelAdmin):
    list_display = ('page_id', 'page_title', 'short_content')

    def short_content(self, obj):
        return obj.content[:200]

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'priority')
    ordering = ('priority', 'id')

@admin.register(Forum)
class ForumAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'priority')
    ordering = ('category__priority', 'category__id', 'priority', 'id')

@admin.register(LatestThreadsForumPreference)
class LatestThreadsForumPreferenceAdmin(admin.ModelAdmin):
    list_display = ('name', 'poster', 'forum', 'include')
    readonly_fields = ('poster',)

    def name(self, obj):
        return str(obj)

class PollOptionInline(admin.TabularInline):
    model = PollOption
    fk_name = 'poll'
    fields = ('answer', 'votes')
    readonly_fields = ('votes',)
    extra = 0

    def votes(self, option):
        return option.votes.count()

@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    list_display = ('question', 'thread',)
    readonly_fields = ('thread', 'vote_type')
    inlines = (PollOptionInline,)

@admin.register(PollVote)
class PollVoteModel(admin.ModelAdmin):
    list_display = ('voter', 'poll_option', 'poll',)
    readonly_fields=('voter', 'poll')

    def poll(self, obj):
        return obj.poll_option.poll

@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ('is_enabled', 'image')


@admin.register(RegistrationCode)
class RegistrationCodeAdmin(admin.ModelAdmin):
    list_display = ('generated_by', 'used_by', 'generated_on', 'used_on',)
    readonly_fields = ('generated_by', 'used_by',)
    list_display
