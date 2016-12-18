import json
import pytz
import uuid
import urllib
import urllib2

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.db import transaction
from django.forms import ValidationError
from django.utils import timezone
from PIL import Image

import utils
from models import *

class UnrenderedInput(forms.widgets.Input):
    def render(self, name, value, attrs=None):
        return ""

class CaptchaForm(forms.Form):
    def clean(self, *args, **kwargs):
        if not utils.get_config('recaptcha_settings'):
            return self.cleaned_data

        captcha_response = self.data.get('g-recaptcha-response', None)

        if not captcha_response:
            raise ValidationError('Please solve the captcha first.')

        req_data = urllib.urlencode({
            'secret': utils.get_config('recaptcha_settings')[1],
            'response': captcha_response
        })

        try:
            resp = urllib2.urlopen(
                'https://www.google.com/recaptcha/api/siteverify',
                req_data,
                1000)

            resp_data = json.load(resp)

            if not resp_data.get('success', False):
                raise ValidationError('Invalid captcha submitted.')

        except ValidationError, e:
            raise
        except e:
            raise ValidationError(
                'Unexpected error occured while validating captcha. Please '
                'try again later.')

        return self.cleaned_data

class NewThreadForm(forms.Form):
    error_css_class = 'in-error'
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
            forum=self.cleaned_data['forum'],
            author=author)

        self.thread.save()

        self.post = Post(
            thread=self.thread,
            content=self.cleaned_data['content'],
            author=author)

        self.post.save()

        return self.thread

class NewPostForm(forms.Form):
    error_css_class = 'in-error'
    post_min_len = utils.get_config('min_post_chars')

    content = forms.CharField(label='Reply',
                              min_length=post_min_len,
                              widget=forms.Textarea())

    thread = forms.ModelChoiceField(queryset=Thread.objects.all(),
                                    widget=forms.HiddenInput())
    _author = None

    def __init__(self, *args, **kwargs):
        if 'author' not in kwargs:
            raise ValueError('Must be inited with a author')

        self._author = kwargs['author']
        del kwargs['author']

        super(NewPostForm, self).__init__(*args, **kwargs)

        self.post = None

    def clean_thread(self):
        thread = self.cleaned_data['thread']

        if not thread.can_reply():
            raise ValidationError('Can not reply to a locked thread')

        return thread

    def clean(self, *args, **kwargs):
        super(NewPostForm, self).clean(*args, **kwargs)
        
        try:
            last_post = self._author.post_set.order_by('-created')[0]
        except IndexError:
            return self.cleaned_data


        if last_post.content == self.cleaned_data.get('content', ''):
            raise ValidationError('Duplicate of your last post.', code='DUPE')

        return self.cleaned_data

    @transaction.atomic
    def save(self):
        self.post = Post(
            thread=self.cleaned_data['thread'],
            content=self.cleaned_data['content'],
            author=self._author)

        self.post.save()

        return self.post

class EditPostForm(forms.Form):
    error_css_class = 'in-error'
    post_min_len = utils.get_config('min_post_chars')

    post = forms.ModelChoiceField(queryset=Post.objects.all(),
                                  widget=forms.HiddenInput())
    
    content = forms.CharField(label='Content',
                              min_length=post_min_len,
                              widget=forms.Textarea())

    def save(self, editor=None):
        post = self.cleaned_data['post']
        post.content = self.cleaned_data['content']

        edit_time = timezone.now() - post.created
        if edit_time.total_seconds() > utils.get_config('ninja_edit_grace_time'):
            editor_name = editor.username if editor else 'unknown'
            post.content += '\n\n[i]Post last edited by %s at %s[/i]' % (
                    editor_name, timezone.now().isoformat())

        post.save()

class ISSAuthenticationForm(AuthenticationForm):
    def clean_username(self):
        """
        Normalize the submitted username and replace the value in cleaned data
        with it's cannonical form. Do nothing if no user with that username
        (or rather normalized image of their username) exists.
        """
        username = self.cleaned_data['username']
        normalized = Poster.normalize_username(username)

        try:
            user = Poster.objects.get(normalized_username=normalized)
        except Poster.DoesNotExist, e:
            return username
        else:
            return user.username

class RegistrationForm(UserCreationForm, CaptchaForm):
    error_css_class = 'in-error'

    class Meta:
        model = Poster
        fields = ('username', 'email')        

    def clean_username(self):
        username = self.cleaned_data['username']
        norm_username = Poster.normalize_username(username)

        if len(norm_username) < 1:
            raise ValidationError('Invalid username', code='INVALID_GENERAL')

        if Poster.objects.filter(normalized_username=norm_username).count():
            raise ValidationError(
                'User with a similar username already exists',
                code='TOO_SIMILAR')

        return username

    def clean(self, *args, **kwargs):
        CaptchaForm.clean(self, *args, **kwargs)

    def save(self, commit=True):   
        poster = super(RegistrationForm, self).save(commit = False)
        poster.save()
        return poster
    
class UserSettingsForm(forms.Form):
    error_css_class = 'in-error'

    email = forms.EmailField(label="Email address")
    timezone = forms.ChoiceField(
            label="Timezone",
            choices=[(tz, tz) for tz in pytz.common_timezones])
    allow_js = forms.BooleanField(label="Enable javascript", required=False)
    allow_avatars = forms.BooleanField(label="Show user avatars", required=False)

    allow_image_embed = forms.BooleanField(
        label="Enable images embedded in posts",
        required=False)

    def save(self, poster):
        poster.email = self.cleaned_data['email']
        poster.allow_js = self.cleaned_data['allow_js']
        poster.allow_avatars = self.cleaned_data['allow_avatars']
        poster.allow_image_embed = self.cleaned_data['allow_image_embed']
        poster.timezone = self.cleaned_data['timezone']

        poster.save()

        return poster

class UserAvatarForm(forms.Form):
    error_css_class = 'in-error'

    avatar = forms.ImageField(required=False)

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')

        if not avatar:
            return

        max_size = utils.get_config('max_avatar_size')
        if avatar.size > max_size:
            raise ValidationError(
                'Image muse be less than %d bytes.' % max_size)

        try:
            image = Image.open(avatar)
            height, width = image.size
        except:
            raise ValidationError('Unexpected error intrepreting image.')
        finally:
            if height > 75 or width > 75:
                raise ValidationError(
                    'Image must be less than or equal to 75px in both width '
                    'and height.')

        return avatar

    def save(self, poster, save=True):
        poster.avatar.delete(save=save)
        poster.avatar = self.cleaned_data['avatar']

        return poster

class NewPrivateMessageForm(forms.Form):
    error_css_class = 'in-error'
    post_min_len = utils.get_config('min_post_chars')
    title_min_len = utils.get_config('min_thread_title_chars')

    subject = forms.CharField(label='Title',
                              max_length=1000,
                              min_length=title_min_len)

    to = forms.CharField(label='To', max_length=512)

    content = forms.CharField(label='Reply',
                              min_length=post_min_len,
                              widget=forms.Textarea())


    _author = None

    def __init__(self, *args, **kwargs):
        if 'author' not in kwargs:
            raise ValueError('Must be inited with a author')

        self._author = kwargs['author']
        del kwargs['author']

        super(NewPrivateMessageForm, self).__init__(*args, **kwargs)

    def clean_to(self):
        to_line = self.cleaned_data['to']

        receivers = []
        unfound = []

        for username in to_line.split(','):
            norm = Poster.normalize_username(username)

            try:
                user = Poster.objects.get(normalized_username=norm)
            except Poster.DoesNotExist:
                error = ValidationError(
                    'User with username %(username)s does not exist.',
                    params={'username': username},
                    code='UNKNOWN_USER')

                unfound.append(error)
            else:
                receivers.append(user)

        if unfound:
            raise ValidationError(unfound)
        else:
            return receivers

    def clean(self, *args, **kwargs):
        super(NewPrivateMessageForm, self).clean(*args, **kwargs)
        
        try:
            last_pm = (PrivateMessage.objects
                .filter(sender=self._author)
                .order_by('-created'))[0]

        except IndexError:
            return self.cleaned_data


        time_since = (timezone.now() - last_pm.created).total_seconds()
        flood_control = utils.get_config('private_message_flood_control')

        if time_since < flood_control:
            raise ValidationError(
                ('Flood control has blocked this message from being sent, '
                 'you can send another PM in %(ttp)d seconds.'),
                params={'ttp': flood_control - time_since},
                code='FLOOD_CONTROL')


        return self.cleaned_data

    @transaction.atomic
    def save(self):
        chain_id = uuid.uuid4()
        sent_copies = []
        kept_copies = []

        for receiver in self.cleaned_data['to']:
            opts = {
                'sender': self._author,
                'receiver': receiver,
                'inbox': receiver,
                'subject': self.cleaned_data['subject'],
                'content': self.cleaned_data['content'],
                'chain': chain_id
            }

            # Receiver's copy
            pm = PrivateMessage(**opts) 
            pm.save()
            sent_copies.append(pm)

            if self._author != receiver:
                # Sender's copy
                opts['inbox'] = self._author
                pm = PrivateMessage(**opts)
                pm.save()
                kept_copies.append(pm)

        return (sent_copies, kept_copies)

class SpamCanUserForm(forms.Form):
    poster = forms.ModelChoiceField(queryset=Forum.objects.all(),
                                    widget=forms.HiddenInput())
    target_form = forms.ModelChoiceField(
        queryset=Forum.objects.filter(is_trash=True),
        required=True)
    next_page = forms.HiddenInput()
