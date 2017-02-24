# python import
import datetime
from pymongo import DESCENDING
from spotipy.client import SpotifyException

# Core Services import
from core import toLog
from core.db import cursor
from config.settings import CAPPED_SIZE
from config.settings import CAPPED_NAME
from config.settings import TRACKS_EXPIRE_TIME as TX
from services.libs.register import register
from services.libs.async_call import asynchronous
from services.plugins.controler.libs.utils import gen_sp


@register
class PlayListCrawl:
    __name__ = 'tracks_crawl'
    __namespace__ = 'ControlerComponent'
    __full_name__ = 'controler.tracks_crawl'
    documentation = """
        Crawl tracks from playlists

        e.g:
        controler.tracks_crawl() > nothing

        Keyword arguments:

        ACL:
            TODO:
    """
    coll_names = cursor.collection_names()

    def allow_time(self):
        now = datetime.datetime.now()
        expire_time = now.replace(hour=TX[0], minute=TX[1])

        if now >= expire_time:
            return False
        else:
            return True

    def fill_capped_collection(self):
        self.create_capped_collection()
        sort = [("followers", DESCENDING)]
        data = cursor.playlist.find().sort(sort).limit(CAPPED_SIZE)

        for doc in data:
            del doc['_id']
            cursor[CAPPED_NAME].insert(doc)

    def set_zero_capped_collection(self):
        cursor[CAPPED_NAME].drop()

    def create_capped_collection(self):
        if CAPPED_NAME not in self.coll_names:
            result = cursor.create_collection(
                CAPPED_NAME,
                capped=True,
                size=5e+8,
                max=CAPPED_SIZE
            )

            if result:
                msg = 'Capped collection "middle" has been created: '
                toLog((msg + str(result)), 'db')

        else:
            self.set_zero_capped_collection()

    def save_tracks(self, tracks, pl):
        for per, track in enumerate(tracks, 1):
            doc = {}
            if 'track' in track and track['track']:

                artists = ""
                for artist in track['track'].get('artists', []):
                    artists += artist['name'] + ", "
                artists = artists[:-2]

                href = track['track'].get('external_urls', {}).get(
                    'spotify',
                    ""
                )
                isrc = track['track'].get('external_ids', {}).get('isrc', '')

                doc['song_name'] = track['track'].get('name', "")
                doc['created_date'] = datetime.datetime.now()
                doc['playlist_name'] = pl['name']
                doc['playlist_followers'] = pl['followers']
                doc['playlist_owner'] = pl['owner_id']
                doc['playlist_href'] = pl['external_url']
                doc['playlist_id'] = pl['playlist_id']
                doc['playlist_description'] = pl['description']
                doc['artist'] = artists.strip()
                doc['href'] = href
                doc['uri'] = track['track'].get('uri', '')
                doc['song_position'] = per
                doc['popularity'] = track['track'].get('popularity', 0)
                doc['isrc'] = isrc
                doc['allbum'] = track['track'].get('album', {}).get('name', '')
                doc['song_id'] = track['track'].get('id', '')
                cursor.tracks.insert(doc)

    @asynchronous
    def run(self, _continue=False):
        if not _continue:
            counter = CAPPED_SIZE
            self.create_capped_collection()
            self.fill_capped_collection()
        else:
            counter = cursor[CAPPED_NAME].count()

        for i in range(counter):
            sort = [("followers", DESCENDING)]
            doc = cursor[CAPPED_NAME].find_one_and_delete({}, sort=sort)

            if doc:
                try:
                    sp = gen_sp()
                except Exception as e:
                    toLog('Spotify API: {}'.format(str(e)), 'error')

                response = sp.user_playlist_tracks(
                    doc['owner_id'],
                    doc['playlist_id'],
                    None,
                    100,
                    0
                )
                tracks = response.get('items', [])
                self.save_tracks(tracks, doc)

                one = 'next' in response and response['next'] is not None
                while one and response.get('next', ''):
                    if not self.allow_time():
                        return

                    try:
                        sp = gen_sp()
                        response = sp.next(response)
                        self.save_tracks(response.get('items', []), doc)

                    except SpotifyException:
                        continue

                    except Exception as e:
                        toLog("{}".format(e), 'error')


PlayListCrawl()
