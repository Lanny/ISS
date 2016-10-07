from django.shortcuts import render

from .models import *

def forum_index(request):
    forums = Forum.objects.all()
    ctx = { 'forums': forums }

    return render(request, 'forum_index.html', ctx)
