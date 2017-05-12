# python import
import time
import datetime
import traceback
from math import ceil
from pymongo import ASCENDING
from pymongo import DESCENDING
from cerberus import Validator
from spotipy.client import SpotifyException
from pymongo.errors import DuplicateKeyError

# Core Services import
from core import toLog
from core.db import cursor
from config.settings import KEYWORD_DAYS
from services.libs.register import register
from config.settings import PLAYLIST_EXPIRE_TIME as PX
from config.settings import FOLLOWERS_CONDS
from services.libs.async_call import asynchronous
from services.plugins.controler.libs.utils import gen_sp
from services.plugins.controler.libs.data_validation import p_schema


@register
class PlayListCrawl:
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
                doc['song_id'] = track['track'].get('id', '')
                doc['playlist_description'] = pl['description']
                doc['artist'] = artists.strip()
                doc['href'] = href
                doc['uri'] = track['track'].get('uri', '')
                doc['song_position'] = per
                doc['popularity'] = track['track'].get('popularity', 0)
                doc['isrc'] = isrc
                doc['allbum'] = track['track'].get('album', {}).get('name', '')

                try:
                    cursor.tracks.insert(doc)
                    self.check_history(doc)
                except DuplicateKeyError:
                    pass
                except:
                    toLog(traceback.format_exc(), 'error')

    def check_history(self, doc):
        new_doc = doc.copy()
        new_doc['action_date'] = datetime.datetime.now()
        last_track = cursor.yesterday.find_one(
            {
                'playlist_id': doc['playlist_id'],
                'song_id': doc['song_id']
            }
        )
        dont_insert = False
        if last_track:
            if last_track['song_position'] != new_doc['song_position']:
                new_doc['action'] = "Changed"
                new_doc['old_position'] = last_track['song_position']
            elif last_track['song_position'] == new_doc['song_position']:
                dont_insert = True
        else:
            new_doc['action'] = 'Add'
            new_doc['old_position'] = None

        if not dont_insert:
            cursor.history.insert(new_doc)

    def drop_action(self):
        counter = cursor.yesterday.count() + 1
        for i in range(counter):
            last_track = cursor.yesterday.find_one_and_delete({})

            if last_track:
                new_track = cursor.tracks.find_one(
                    {
                        'playlist_id': last_track['playlist_id'],
                        'song_id': last_track['song_id']
                    }
                )
                if not new_track:
                    last_track['action'] = 'Drop'
                    last_track['old_position'] = last_track['song_position']
                    last_track['song_position'] = None
                    last_track['action_date'] = datetime.datetime.now()
                    cursor.history.insert(last_track)

    def save_to_db(self, playlists):
        ids = []
        for doc in playlists:
            data = {}
            try:
                if ('id' in doc) and doc['id']:
                    data['playlist_id'] = doc['id']
                else:
                    toLog("{}".format(doc), 'lost_ids')
                    continue

                try:
                    data['name'] = doc.get('name', '').strip()
                except AttributeError:
                    data['name'] = ''

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
                cursor.playlist.replace_one(
                    {'playlist_id': data['playlist_id']},
                    data,
                    upsert=True
                )
                ids.append(data)

            except AttributeError:
                pass

        try:
            # Start Update info Playlist
            self.update_info(ids)
        except:
            toLog(traceback.format_exc(), 'error')

    def move_to_yesterday(self):
        cursor.yesterday.delete_many({})
        data = cursor.tracks.find({}, {'_id': 0}, no_cursor_timeout=True)
        for doc in data:
            doc.pop('_id')
            cursor.yesterday.insert(doc)
        cursor.tracks.delete_many({})
        self.ensure_indexes()
        return True

    def fetch_sp(self):
        while True:
            try:
                time.sleep(1.5)
                sp = gen_sp()
                return sp
            except:
                toLog(traceback.format_exc(), 'error')

    def update_info(self, ids):
        for doc in ids:
            sp = self.fetch_sp()

            try:
                result = sp.user_playlist(
                    doc['owner_id'],
                    doc['playlist_id']
                )
                if not result:
                    return

                followers = result.get('followers', {}).get('total', 0)
                _update = {
                    'modified_date': datetime.datetime.now(),
                    'description': result.get('description', ''),
                    'followers': followers
                }
                cursor.playlist.update_one(
                    {
                        'playlist_id': doc['playlist_id'],
                        'owner_id': doc['owner_id'],
                    },
                    {'$set': _update}
                )

                if followers >= FOLLOWERS_CONDS:
                    if 'tracks' in result:
                        doc['followers'] = followers
                        doc['description'] = result.get('description', '')
                        if result['tracks'].get('items', []):
                            self.save_tracks(result['tracks']['items'], doc)

                        response = result['tracks']
                        while response.get('next', ''):
                            try:
                                response = sp.next(response)
                                tracks = response.get('items', [])
                                self.save_tracks(tracks, doc)

                            except SpotifyException:
                                continue

                            except Exception as e:
                                toLog("{}".format(e), 'error')

            except SpotifyException:
                toLog(traceback.format_exc(), 'error')

            except:
                toLog(traceback.format_exc(), 'error')

    def crawl_playlist(self):
        now = datetime.datetime.now()
        expected = now - datetime.timedelta(days=KEYWORD_DAYS)
        criteria = {}
        keywords = list(cursor.keywords.find(criteria))

        for doc in keywords:
            if not self.allow_time():
                return

            if expected >= doc['turn_date']:
                sp = self.fetch_sp()
                response = sp.search(
                    q=doc['word'],
                    limit=50,
                    type='playlist',
                    offset=0
                )

                # if doc['loop'] <= 1:
                #     sp = self.fetch_sp()
                #     response = sp.search(
                #         q=doc['word'],
                #         limit=50,
                #         type='playlist',
                #         offset=0
                #     )

                # elif doc['loop'] < doc['loops']:
                #     # Generate new token
                #     sp = self.fetch_sp()
                #     response = sp.search(
                #         q=doc['word'],
                #         limit=50,
                #         type='playlist',
                #         offset=(50 * int(doc['loop']))
                #     )

                if response:
                    doc['total'] = response['playlists'].get('total', 0)
                    doc['loops'] = int(ceil(doc['total'] / 50.0))
                    doc['turn_date'] = now
                    doc['loop'] = 1
                    cursor.keywords.update_one(
                        {'_id': doc['_id']},
                        {'$set': doc}
                    )
                    self.save_to_db(response['playlists'].get('items', []))
                    loop_counter = 0

                    _val = Validator(p_schema)
                    while _val.validate(response) and response.get('playlists', {}).get('next', ''):
                        if loop_counter >= 2:
                            break
                        else:
                            loop_counter += 1

                        if not self.allow_time():
                            return

                        try:
                            sp = self.fetch_sp()
                            response = sp.next(response['playlists'])
                            doc['turn_date'] = now
                            doc['loop'] += 1
                            cursor.keywords.update_one(
                                {'_id': doc['_id']},
                                {'$set': doc}
                            )
                            self.save_to_db(
                                response.get('playlists', {}).get('items', [])
                            )
                        except SpotifyException:
                            toLog(traceback.format_exc(), 'error')
                            continue

                        except:
                            toLog(traceback.format_exc(), 'error')

            else:
                toLog("Out of turn date: {}".format(doc), 'error')
                continue

    def ensure_indexes(self):
        cursor.yesterday.create_index(
            [('playlist_id', DESCENDING), ('song_id', ASCENDING)]
        )
        cursor.tracks.create_index(
            [('playlist_id', DESCENDING), ('song_id', ASCENDING)]
        )
        cursor.tracks.create_index(
            [("playlist_id", DESCENDING), ("song_id", DESCENDING)],
            unique=True
        )

    @asynchronous
    def run(self):
        # If the now time reach to expire time
        if not self.allow_time():
            return
        # Move tracks to Yesterday
        if not self.move_to_yesterday():
            return
        # Start main way
        self.crawl_playlist()
        # Final action
        self.drop_action()


PlayListCrawl()
