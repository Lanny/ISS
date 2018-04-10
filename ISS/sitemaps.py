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
    @staticmethod
    def _lazy_last_post(thread, n):
        return lambda: thread.get_posts_in_thread_order()[n]

    def items(self):
        pages = []
        threads = Thread.objects.filter(forum__is_trash=False)

        for thread in threads:
            ppp = utils.get_config('posts_per_thread_page')
            post_count = thread.get_post_count()
            num_pages = int(math.ceil(post_count / ppp))

            for n in range(1,num_pages+1):
                url = thread.get_url(page=n)
                last_page = n == num_pages
                last_idx = (post_count if last_page else n*ppp) - 1
                last_post = self._lazy_last_post(thread, last_idx)

                pages.append((thread, url, last_page, last_post))

        return pages

    def changefreq(self, data):
        thread, url, last_page, last_post = data
        if last_page:
            inactive_time = timezone.now() - thread.last_update
            if  inactive_time < timedelta(days=1):
                return 'hourly'
            elif  inactive_time < timedelta(days=28):
                return 'daily'
            else:
                return 'monthly'
        else:
            return 'never'

    def lastmod(self, data):
        thread, url, last_page, last_post = data
        return last_post().created
    
    def location(self, data):
        thread, url, last_page, last_post = data
        return url

iss_sitemaps = {
    'forums': ForumsSitemap,
    'threads': ThreadSitemap
}
    
