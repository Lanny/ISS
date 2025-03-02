import random
import io
import base64

from django import forms
from django.core.cache import cache, caches
from django.core.cache.backends.base import InvalidCacheBackendError
from PIL import Image, ImageDraw, ImageEnhance


'''
A hacky bid at builing a low effort but (hopefully) unique captcha system. A
captcha consists of noise with a white circle drawn in each cell of a 9x9 grid.
Solving the captcha involves identifying which cells in the grid are contain
the said circles. While this isn't exactly a hard CV problem, it hope is that
the added circles don't produce consistently detectable deviation from the
statistical mean in each cell, and thus trivial solutions aren't possible. Does
this actually work? Time will tell.
'''

# Use db_cache if specified, otherwise the default cache. Note that if we have
# to use LocMemCache this breakds down pretty badly, the scheme here assumes
# access to a cache that exists across processes.
captcha_cache = cache 
try:
    captcha_cache = caches['db_cache']
except InvalidCacheBackendError:
    print('No `db_cache` exists, this could be a problem if you\'re using LocMemCache')

def create_captcha(cells):
    # Create iamge where pixels are randomly assigned black or white
    im = Image.effect_noise((300, 300), 64.0)
    im = ImageEnhance.Sharpness(im).enhance(256.0)

    # Draw a white circle in each specified cell, offset by some random jitter
    draw = ImageDraw.Draw(im)
    for cell in cells:
        cx, cy = cell

        if cx > 2 or cx < 0 or cy > 2 or cy < 0:
            raise Exception(
                    'Cell (%s, %s) has a component not in [0,2]' % (cx, cy))

        px = (cx * 100) + 50 + random.randrange(-10, 11)
        py = (cy * 100) + 50 + random.randrange(-10, 11)

        draw.circle((px, py), 30, outline=256, width=2)

    return im

def create_challenge():
    challenge_id = random.randint(0, 2**32)
    solution = set([
        (random.randrange(0,3), random.randrange(0,3))
        for _ in range(random.randrange(2,9))
    ])
    captcha_image = create_captcha(solution)
    captcha_cache.set('captcha_challenge:%s' % challenge_id, solution)

    return (challenge_id, captcha_image)

class CaptchaForm(forms.Form):
    template_name = 'forms/captcha_form.html'
    challenge_id = None
    captcha_data_url = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            challenge_id, captcha_image = create_challenge()
            self.challenge_id = challenge_id

            buf = io.BytesIO()
            captcha_image.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
            self.captcha_data_url = 'data:image/png;base64,' + b64

    def clean(self, data, *args, **kwargs):
        solution = captcha_cache.get(
            'captcha_challenge:%s' % data.get('challenge_id'))

        if not solution:
            raise ValidationError('Invalid captcha', code='NO_CHALLENGE')

        for cx, cy in solution:
            if data.get('c_%d_%d' % (cx, cy), None) != 'on':
                raise ValidationError('Invalid captcha', code='INVALID_CAPTCHA')

        result = super().clean(data, *args, **kwargs)


        return result

            

'''
class CaptchaWidget(forms.Widget):
    template_name = "django/forms/widgets/hidden.html"

    def __init__(self, challenge_id, captcha_image):
        self.challenge_id = challenge_id
        self.captcha_image = captcha_image
        super().__init__()

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["widget"]["challenge_id"] = self.challenge_id
        context["widget"]["captcha_image"] = self.captcha_image
        return context

class CaptchaField(forms.Field):
    def __init__(self, *, **kwargs):
        kwargs['widget'] = CaptchaWidget()
        super().__init__(**kwargs)

    def clean(self, value):
        value = super(CaptchaField, self).clean(value)

'''
