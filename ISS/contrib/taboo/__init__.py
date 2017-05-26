from datetime import timedelta

default_app_config = 'ISS.contrib.taboo.apps.TabooConfig'

ISS_config = {
    'violation_duration': timedelta(days=1),
    'ban_reason_tmpl': 'You said the taboo phrase "%(phrase)s"!',
    'post_msg_tmpl': '\n\n[b]User was banned for saying the taboo phrase "%(phrase)s"![/b]'
}
