import random

import mysql.connector

from django.db.utils import IntegrityError
from django.core.management.base import BaseCommand, CommandError
from ISS.models import *

class Command(BaseCommand):
    help = 'Migrates a vBulletin 5 database to ISS'

    def add_arguments(self, parser):
        # parser.add_argument('n', type=int)
        pass

    def handle(self, *args, **kwargs):
        db_user = 'root'
        db_pass = ''
        db_name = 'vB'
        db_host = 'localhost'

        cnx = mysql.connector.connect(user=db_user,
                                      password=db_pass,
                                      host=db_host,
                                      database=db_name)
        cursor = cnx.cursor(dictionary=True)
        query = 'SELECT * FROM user;'
        cursor.execute(query)

        o2n_map = {}
        for user in cursor:
            new_user = Poster(username=user['username'],
                              email=user['email'])
            try:
                new_user.save()
                o2n_map[user['userid']] = new_user
            except IntegrityError:
                print 'Duplicate, could not save user: %s' % user['username']
                o2n_map[user['userid']] = Poster.objects.get(username=user['username'])

        
        cnx.close()

        
