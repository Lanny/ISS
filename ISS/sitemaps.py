import math
from datetime import timedelta

from django.contrib.sitemaps import Sitemap
from django.utils import timezone

from ISS.models import *

class ForumsSitemap(Sitemap):
    changefreq = 'daily'
    priority = 1.0

    def items(self):
        return Forum.objects.filter(is_trash=False)

    def lastmod(self, forum):
        return forum.last_update
    
    def location(self, forum):
        return forum.get_url()

class ThreadSitemap(Sitemap):
    def items(self):
        return Thread.objects.filter(forum__is_trash=False)

    def changefreq(self, thread):
        inactive_time = timezone.now() - thread.last_update
        if  inactive_time < timedelta(days=1):
            return 'hourly'
        elif  inactive_time < timedelta(days=28):
            return 'daily'
        else:
            return 'monthly'

    def lastmod(self, thread):
        return thread.last_update
    
    def location(self, thread):
        return thread.get_url()

iss_sitemaps = {
    'forums': ForumsSitemap,
    'threads': ThreadSitemap
}
    
