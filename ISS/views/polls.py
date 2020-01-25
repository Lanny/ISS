from django.shortcuts import render, get_object_or_404
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.db import transaction

from ISS import utils, forms
from ISS.models import Thread, Poll, PollOption

class CreatePoll(utils.MethodSplitView):
    active_required = True

    def pre_method_check(self, request, thread_id):
        thread = get_object_or_404(Thread, pk=thread_id)

        if thread.author != request.user:
            raise PermissionDenied()

        try:
            poll = thread.poll
        except Poll.DoesNotExist:
            pass
        else:
            # Thread already has a poll, this request is in error
            raise PermissionDenied()

        return {'thread': thread}

    def GET(self, request, thread_id, thread=None):
        form = forms.NewPollForm(initial={'thread': thread})

        return render(request, 'new_poll.html', {
            'thread': thread,
            'form': form
        })

    @transaction.atomic
    def POST(self, request, thread_id, thread):
        form = forms.NewPollForm(request.POST)

        if form.is_valid():
            poll = Poll.objects.create(
                thread=thread,
                question=form.cleaned_data['question'],
                vote_type=form.cleaned_data['vote_type']
            )

            for answer in form.get_cleaned_options():
                PollOption.objects.create(
                    poll=poll,
                    answer=answer
                )

            return HttpResponseRedirect(thread.get_url())

        else:
            return render(request, 'new_poll.html', {
                'thread': thread,
                'form': form
            })
