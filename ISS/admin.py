from django.contrib import admin

from .models import *

admin.site.register(Poster)
admin.site.register(Forum)
admin.site.register(Thread)
admin.site.register(Post)
admin.site.register(Thanks)

@admin.register(PrivateMessage)
class PrivateMessageAdmin(admin.ModelAdmin):
    list_display = ('subject', 'sender', 'receiver', 'created')
