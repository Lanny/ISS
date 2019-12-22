from django.contrib import admin

from .models import *

@admin.register(TabooProfile)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('poster', 'mark', 'phrase', 'active')
