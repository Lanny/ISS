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

    def get_options(self):
        return (PollOption.objects
            .all()
            .filter(poll=self)
            .prefetch_related('votes'))

    def get_vote_distribution(self):
        return {opt: len(opt.votes.all()) for opt in self.get_options()}


class PollOption(models.Model):
    poll = models.ForeignKey(Poll, null=False, on_delete=models.CASCADE)
    answer = models.CharField(max_length=1024)


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
