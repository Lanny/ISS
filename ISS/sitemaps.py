from django.contrib.sitemaps import Sitemap

from ISS.models import *

class ForumsSitemap(Sitemap):
    changefreq = 'monthly'

    def items(self):
        return Forum.objects.filter(is_trash=False)

    def lastmod(self, forum):
        return forum.last_update
    
    def location(self, forum):
        return forum.get_url()

iss_sitemaps = {
    'forums': ForumsSitemap
}
    
