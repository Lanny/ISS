from django import forms
from django.contrib.auth.forms import UserCreationForm      
from django.db import transaction
from django.forms import ValidationError

import utils
from models import Forum, Thread, Post, Poster

class NewThreadForm(forms.Form):
    thread_min_len = utils.get_config('min_thread_title_chars')
    post_min_len = utils.get_config('min_post_chars')

    title = forms.CharField(label='Title',
                            max_length=1000,
                            min_length=thread_min_len)

    content = forms.CharField(label='Post Body',
                              min_length=post_min_len,
                              widget=forms.Textarea())

    forum = forms.ModelChoiceField(queryset=Forum.objects.all(),
                                   widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super(NewThreadForm, self).__init__(*args, **kwargs)

        self.thread = None
        self.post = None

    @transaction.atomic
    def save(self, author):
        self.thread = Thread(
            title=self.cleaned_data['title'],
            forum=self.cleaned_data['forum'])

        self.thread.save()

        self.post = Post(
            thread=self.thread,
            content=self.cleaned_data['content'],
            author=author)

        self.post.save()

        return self.thread

class NewPostForm(forms.Form):
    post_min_len = utils.get_config('min_post_chars')

    content = forms.CharField(label='Reply',
                              min_length=post_min_len,
                              widget=forms.Textarea())

    thread = forms.ModelChoiceField(queryset=Thread.objects.all(),
                                    widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super(NewPostForm, self).__init__(*args, **kwargs)

        self.post = None

    def clean_thread(self):
        thread = self.cleaned_data['thread']

        if not thread.can_reply():
            raise ValidationError('Can not reply to a locked thread')

        return thread

    @transaction.atomic
    def save(self, author):
        self.post = Post(
            thread=self.cleaned_data['thread'],
            content=self.cleaned_data['content'],
            author=author)

        self.post.save()

        return self.post


class RegistrationForm(UserCreationForm):
    class Meta:
        model = Poster
        fields = ('username', 'email')        

    def save(self,commit = True):   
        poster = super(RegistrationForm, self).save(commit = False)
        poster.save()
        return poster
    
