from django.contrib import admin

from .models import *

class ForumInline(admin.TabularInline):
    model = Forum
    extra = 0

admin.site.register(Thanks)
admin.site.register(AuthPackage)
admin.site.register(RegistrationCode)
admin.site.register(PostSnapshot)

class BanInline(admin.TabularInline):
    model = Ban
    fk_name = 'subject'
    extra = 0

@admin.register(Poster)
class PosterAdmin(admin.ModelAdmin):
    exclude = ('avatar',)
    inlines = [BanInline]

@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    readonly_fields = ('author',)

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('author', 'thread_name', 'short_content')
    readonly_fields = ('author',)

    def thread_name(self, obj):
        return obj.thread.title[:100]

    def short_content(self, obj):
        return obj.content[:200]

    def get_readonly_fields(self, request, obj=None):
        return self.readonly_fields + ('thread', 'author')
    

@admin.register(PrivateMessage)
class PrivateMessageAdmin(admin.ModelAdmin):
    list_display = ('subject', 'sender', 'receiver', 'created')

@admin.register(FilterWord)
class FilterWordAdmin(admin.ModelAdmin):
    list_display = ('pattern', 'replacement', 'active')

@admin.register(Ban)
class BanAdmin(admin.ModelAdmin):
    list_display = ('subject', 'reason', 'start_date', 'end_date', 'given_by')

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

    def name(self, obj):
        return unicode(obj)

