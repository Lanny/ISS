from django.shortcuts import render, get_object_or_404

from ISS import utils, forms
from ISS.models import Thread

class CreatePoll(utils.MethodSplitView):
    def GET(self, request, thread_id):
        thread = get_object_or_404(Thread, pk=thread_id)
        form = forms.NewPollForm(initial={'thread': thread})


        return render(request, 'new_poll.html', {
            'thread': thread,
            'form': form
        })

    def POST(self, request, thread_id):
        thread = get_object_or_404(Thread, pk=thread_id)

        if thread.author != request.user:
            raise PermissionDenied()

        return None
