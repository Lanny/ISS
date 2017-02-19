from django.contrib import admin

from .models import *

admin.site.register(Forum)
admin.site.register(Thread)
admin.site.register(Thanks)

@admin.register(Poster)
class PosterAdmin(admin.ModelAdmin):
    exclude = ('avatar',)

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

