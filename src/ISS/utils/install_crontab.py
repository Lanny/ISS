from crontab import CronTab

from ISS import utils

MAGIC = "ISS_hot_topics_updating"

def install_crontab():
    cron = CronTab(user=True)
