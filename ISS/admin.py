from django.contrib import admin

from .models import *

class ForumInline(admin.TabularInline):
    model = Forum
    extra = 0

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'priority')

admin.site.register(Forum)
admin.site.register(Thread)
admin.site.register(Thanks)

class BanInline(admin.TabularInline):
    model = Ban
    fk_name = 'subject'
    extra = 0

@admin.register(Poster)
class PosterAdmin(admin.ModelAdmin):
    exclude = ('avatar',)
    inlines = [BanInline]

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('author', 'thread_name', 'short_content')

    def thread_name(self, obj):
        return obj.thread.title[:100]

    def short_content(self, obj):
        return obj.content[:200]

@admin.register(PrivateMessage)
class PrivateMessageAdmin(admin.ModelAdmin):
    list_display = ('subject', 'sender', 'receiver', 'created')

@admin.register(FilterWord)
class FilterWordAdmin(admin.ModelAdmin):
    list_display = ('pattern', 'replacement', 'active')

@admin.register(Ban)
class BanAdmin(admin.ModelAdmin):
    list_display = ('subject', 'reason', 'start_date', 'end_date', 'given_by')


