import hashlib

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

model_backend = ModelBackend()

class vB5_legacy(object):
    def __init__(self):
        if 'md5' not in hashlib.algorithms_available:
            raise Exception(
                'vb5_legacy autentication backend requires md5 support from '
                'hashlib or it will not run.')

    def authenticate(self, username=None, password=None, **kwargs):
        UserModel = get_user_model()

        unsalted_pass = hashlib.new('md5')
        unsalted_pass.update(password)
        unsalted_digest = unsalted_pass.hexdigest()

        try:
            user = UserModel._default_manager.get_by_natural_key(username)
        except UserModel.DoesNotExist:
            UserModel().set_password(password)
            return None

        try:
            phash, salt = user.password.split(' ')
        except ValueError:
            return None
        else:
            salted_pass = hashlib.new('md5')
            salted_pass.update(unsalted_digest + salt)

            if salted_pass.hexdigest() == phash:
                if getattr(settings, 'vB5_UPGRADE_AUTH', True):
                    self._upgrate_user_auth(user, password)

                return user
            else:
                return None

    def _upgrate_user_auth(self, user, raw_password):
        user.set_password(raw_password)
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        user.save(update_fields=['password', 'backend'])

    def get_user(self, *args, **kwargs):
        return model_backend.get_user(*args, **kwargs)
