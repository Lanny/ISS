from django.shortcuts import render, get_object_or_404
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.db import transaction

from ISS import utils, forms
from ISS.views.forum import thread
from ISS.models import Thread, Poll, PollOption, PollVote


class CreatePoll(utils.MethodSplitView):
    error_css_class = 'in-error'
    active_required = True
    unbanned_required = True

    def pre_method_check(self, request, thread_id):
        thread = get_object_or_404(Thread, pk=thread_id)

        if thread.author != request.user:
            raise PermissionDenied('Only thread authors can create polls')

        if thread.get_poll():
            raise PermissionDenied('Thread already has a poll')

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


class CastVote(utils.MethodSplitView):
    require_login = True
    active_required = True
    unbanned_required = True

    @transaction.atomic
    def POST(self, request, poll_id):
        poll = get_object_or_404(Poll, pk=poll_id)

        if not poll.poster_can_vote(request.user):
            raise PermissionDenied('Can not vote.')

        form = forms.CastVoteForm(request.POST, poll=poll)

        if form.is_valid():
            for option in form.get_cleaned_options():
                PollVote.objects.create(poll_option=option, voter=request.user)

            return HttpResponseRedirect(poll.thread.get_url())
        else:
            return thread(request, poll.thread_id, poll_vote_form=form)
