from django.db import models


class Poll(models.Model):
    SINGLE_CHOICE = 0
    MULTIPLE_CHOICE = 1

    VOTE_TYPE_CHOICES = (
        (SINGLE_CHOICE, 'Single Choice Voting'),
        (MULTIPLE_CHOICE, 'Multiple Choice Voting'),
    )

    thread = models.OneToOneField('ISS.Thread', on_delete=models.CASCADE)
    question = models.CharField(max_length=1024)
    vote_type = models.IntegerField(
        choices=VOTE_TYPE_CHOICES,
        default=SINGLE_CHOICE,
        blank=False,
        null=False)

    def poster_can_vote(self, poster):
        return (not self.poster_has_voted(poster)
                and not self.thread.locked)

    def poster_has_voted(self, poster):
        return bool(PollVote.objects
            .filter(voter=poster, poll_option__poll=self)
            .count())

    def get_options(self):
        return (PollOption.objects
            .all()
            .filter(poll=self)
            .prefetch_related('votes'))

    def get_vote_distribution(self):
        return {opt: len(opt.votes.all()) for opt in self.get_options()}

    def get_vote_distribution_percentages(self):
        opts = self.get_options()
        denom = 1.0 * (sum((len(opt.votes.all()) for opt in opts)) or 1)
        return {opt: len(opt.votes.all()) * 100.0 / denom for opt in opts}

    def __str__(self):
        return 'Poll: %s' % self.question


class PollOption(models.Model):
    poll = models.ForeignKey(Poll, null=False, on_delete=models.CASCADE)
    answer = models.CharField(max_length=1024)

    def __str__(self):
        return self.answer


class PollVote(models.Model):
    class Meta:
        unique_together = ('poll_option', 'voter')

    poll_option = models.ForeignKey(
        PollOption,
        related_name='votes',
        null=False,
        on_delete=models.CASCADE)
    voter = models.ForeignKey(
        'ISS.Poster',
        null=False,
        on_delete=models.CASCADE)
