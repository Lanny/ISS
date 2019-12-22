import random
import pytz
from datetime import datetime

import mysql.connector

from django.db.models import Count
from django.db.utils import IntegrityError
from django.core.management.base import BaseCommand, CommandError
from ISS.models import *

migration_version = 'DEVELOPMENT_001'
utc = pytz.timezone('utc')

class Command(BaseCommand):
    help = ('Migrates a vBulletin 5 database to ISS. Source database location '
            'and credentials must be supplied, target database info is picked '
            'up from settings.py. NB: this process is only idempotent over '
            'the users table.')

    def add_arguments(self, parser):
        parser.add_argument('--db-host', default='localhost',
                            help='Host for the source database')
        parser.add_argument('--db-port', default=3306, type=int,
                            help='Port to connect to the source DB on')
        parser.add_argument('--db-name', 
                            help='Name of the source database to connect to')
        parser.add_argument('--db-user', 
                            help='User to log into the source database as')
        parser.add_argument('--db-pass', default='',
                            help='Password for the specified user')
        parser.add_argument('--mig-thanks', action='store_true',
                            help='Migrate dbtech thanks entries')

    def mig_users(self, cnx, cursor):
        query = 'SELECT * FROM user;'
        cursor.execute(query)

        o2n_map = {}
        for user in cursor:
            new_user = Poster(username=user['username'],
                              email=user['email'],
                              password=user['token'],
                              backend='ISS.auth.backends.vB5_%s' % user['scheme'])
            try:
                new_user.save()
                o2n_map[user['userid']] = new_user.pk
            except IntegrityError:
                o2n_map[user['userid']] = Poster.objects.get(
                    username=user['username']).pk

        return o2n_map

    def mig_forums(self, cnx, cursor):
        query = """
            SELECT forum.* FROM node AS forum
                JOIN node AS forum_group
                    ON forum.parentid = forum_group.nodeid
                JOIN node AS forum_parent
                    ON forum_group.parentid = forum_parent.nodeid
                WHERE
                    forum_parent.urlident = 'forum'
        """

        cursor.execute(query)
        o2n_map = {}
        for forum in cursor:
            new_forum = Forum(
                name=forum['title'],
                description=forum['description'],
                priority=forum['displayorder'])

            new_forum.save()

            o2n_map[forum['nodeid']] = new_forum.pk

        return o2n_map

    def mig_threads(self, cnx, cursor, forum_pk_map, user_pk_map):
        cursor.execute("""
            SELECT thread.* FROM node AS thread
                JOIN node AS forum
                    ON thread.parentid=forum.nodeid
                JOIN node AS forum_group
                    ON forum.parentid=forum_group.nodeid
                JOIN node AS forum_parent
                    ON forum_parent.nodeid=forum_group.parentid 
                WHERE 
                    forum_parent.urlident = 'forum'
        """)

        thread_map = {}
        post_map = {}

        threads = cursor.fetchall()
        for thread in threads:
            new_thread = Thread(
                title=thread['title'],
                created=datetime.fromtimestamp(thread['publishdate'], utc),
                forum_id=forum_pk_map[thread['parentid']],
                log='Migrated at %s' % migration_version,
                last_update=datetime.fromtimestamp(0, utc))

            new_thread.save()

            cursor.execute('SELECT * FROM text WHERE nodeid=%s',
                           (thread['nodeid'],))

            first = True
            for result in cursor:
                if not first:
                    raise Exception('Wowah there')

                first = False

                op_text = result['rawtext']

                new_post = Post(
                    created=datetime.fromtimestamp(thread['publishdate'], utc),
                    thread_id=new_thread.pk,
                    content=op_text,
                    author_id=user_pk_map[thread['userid']])

            new_post.save()

            thread_map[thread['nodeid']] = new_thread.pk
            post_map[thread['nodeid']] = new_post.pk

        return thread_map, post_map

    def mig_posts(self, cnx, cursor, thread_pk_map, user_pk_map):
        o2n_map = {}

        for old_thread_id in thread_pk_map:
            cursor.execute("""
                SELECT post.*, text.rawtext FROM node AS post
                    JOIN text
                        ON text.nodeid=post.nodeid
                    WHERE
                        post.parentid=%s
            """, (old_thread_id,))

            for post in cursor:
                new_post = Post(
                    created=datetime.fromtimestamp(post['publishdate'], utc),
                    thread_id=thread_pk_map[old_thread_id],
                    content=post['rawtext'],
                    author_id=user_pk_map[post['userid']])

                new_post.save()
                o2n_map[post['nodeid']] = new_post.pk

        return o2n_map

    def mig_thanks(self, cnx, cursor, user_pk_map, post_pk_map):
        cursor.execute("""
            SELECT contentid, userid, receiveduserid FROM dbtech_thanks_entry
                WHERE varname='thanks'
                GROUP BY contentid, userid, receiveduserid
        """)

        for thanks in cursor:
            try:
                post_id = post_pk_map[thanks['contentid']]
            except KeyError:
                print(('Error migrating thanks: post %d was not found'
                       % thanks['contentid']))
            else:
                new_thanks = Thanks(
                    thanker_id=user_pk_map[thanks['userid']],
                    thankee_id=user_pk_map[thanks['receiveduserid']],
                    post_id=post_id)

                try:
                    new_thanks.save()
                except IntegrityError as e:
                    import pdb; pdb.set_trace()

        return

    def handle(self, db_user=None, db_port=None, db_host=None, db_pass=None,
            db_name=None, mig_thanks=False, **kwargs):
        cnx = mysql.connector.connect(user=db_user,
                                      password=db_pass,
                                      host=db_host,
                                      port=db_port,
                                      database=db_name)
        cursor = cnx.cursor(dictionary=True, buffered=True)

        print('Migrating users...')
        user_pk_map = self.mig_users(cnx, cursor)

        print('Done.\nMigrating forums...')
        forum_pk_map = self.mig_forums(cnx, cursor)

        print('Done.\nMigrating threads...')
        thread_pk_map, op_pk_map = self.mig_threads(cnx, cursor, forum_pk_map,
                                                    user_pk_map)

        print('Done.\nMigrating posts...')
        post_pk_map = self.mig_posts(cnx, cursor, thread_pk_map, user_pk_map)

        if mig_thanks:
            print('Done.\nMigrating thanks...')
            post_pk_map.update(op_pk_map)
            self.mig_thanks(cnx, cursor, user_pk_map, post_pk_map)

        print('Done.')
        
        cnx.close()
