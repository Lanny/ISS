from django.utils import timezone
from datetime import datetime, timedelta
from ISS.models import *

def tstm(poster):
    junk_user = Poster.get_or_create_junk_user()
    poster.merge_into(junk_user)
    poster.is_active = False
    poster.save()

    print('Successfully anonymized user with id: %d' % poster.pk)

print('Django\'s `timezone`, datetimes\'s `datetime` and `timedelta`, and '
      'all of the ISS models have been imported and are currently in scope. '
      'The tstm() function has also been made available.')
