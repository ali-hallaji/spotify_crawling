# python import
import datetime
from math import ceil
from spotipy.client import SpotifyException

# Core Services import
from core import toLog
from core.db import cursor
from config.settings import KEYWORD_DAYS
from services.libs.register import register
from config.settings import PLAYLIST_EXPIRE_TIME as PX
from services.libs.async_call import asynchronous
from services.plugins.controler.libs.utils import gen_sp


@register
class PlayListCrawl:
    """
        Stop Server
    """
    __name__ = 'playlist_crawl'
    __namespace__ = 'ControlerComponent'
    __full_name__ = 'controler.playlist_crawl'
    documentation = """
        Crawl play lists from keywords

        e.g:
        controler.playlist_crawl() > nothing

        Keyword arguments:

        ACL:
            TODO:
    """

    def allow_time(self):
        now = datetime.datetime.now()
        expire_time = now.replace(hour=PX[0], minute=PX[1])

        if now >= expire_time:
            return False
        else:
            return True

    def save_to_db(self, playlists):
        for doc in playlists:
            data = {}

            if 'id' in doc.get('id', None):
                data['playlist_id'] = doc['id']
            else:
                toLog("{}".format(doc), 'lost_ids')
                continue

            data['name'] = doc.get('name', '').strip()
            data['created_date'] = datetime.datetime.now()
            data['href'] = doc.get('href', None)
            data['external_url'] = doc.get('external_urls', {}).get(
                'spotify', None
            )
            data['uri'] = doc.get('uri', None)
            data['owner_external_url'] = doc.get('owner', {}).get(
                'external_urls', {}).get('spotify', None)
            data['owner_id'] = doc.get('owner', {}).get('id', None)
            data['owner_href'] = doc.get('owner', {}).get('href', None)
            data['owner_uri'] = doc.get('owner', {}).get('uri', None)
            result = cursor.playlist.replace_one(
                {'playlist_id': data['playlist_id']},
                data,
                upsert=True
            )
            log = 'Insert: (playlist_id = {}) --result-- {}'.format(
                data['playlist_id'],
                result.raw_result
            )
            toLog(log, 'db')

    @asynchronous
    def run(self):
        if not self.allow_time():
            return

        now = datetime.datetime.now()
        expected = now - datetime.timedelta(days=KEYWORD_DAYS)
        criteria = {}
        keywords = cursor.keywords.find(criteria)

        for doc in keywords:
            if expected >= doc['turn_date']:
                # Generate new token
                sp = gen_sp()
                response = sp.search(
                    q=doc['word'],
                    limit=50,
                    type='playlist',
                    offset=0
                )

            elif doc['loop'] < doc['loops']:
                # Generate new token
                sp = gen_sp()
                response = sp.search(
                    q=doc['word'],
                    limit=50,
                    type='playlist',
                    offset=(50 * int(doc['loop']))
                )
            else:
                toLog("Error while loop: {}".format(doc), 'error')
                continue

            if 'playlists' in response:
                doc['total'] = response['playlists'].get('total', 0)
                doc['loops'] = int(ceil(doc['total'] / 50.0))
                doc['turn_date'] = now
                doc['loop'] = 1
                cursor.keywords.update_one(
                    {'_id': doc['_id']},
                    {'$set': doc}
                )
                self.save_to_db(response['playlists'].get('items', []))

                while ('playlists' in response) and (response['playlists'].get('next', '')):
                    if not self.allow_time():
                        return

                    try:
                        sp = gen_sp()
                        response = sp.next(response['playlists'])
                        doc['turn_date'] = now
                        doc['loop'] += 1
                        cursor.keywords.update_one(
                            {'_id': doc['_id']},
                            {'$set': doc}
                        )
                        self.save_to_db(
                            response['playlists'].get('items', [])
                        )
                    except SpotifyException:
                        continue

                    except Exception as e:
                        toLog("{}".format(e), 'error')


PlayListCrawl()
