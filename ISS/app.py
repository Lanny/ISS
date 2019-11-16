from django.apps import AppConfig
from django.core.cache import cache

class ISSConfig(AppConfig):
    name = 'ISS'
    verbose_name = 'ISS'

    def ready(self):
        cache.clear()
        import ISS.signals
