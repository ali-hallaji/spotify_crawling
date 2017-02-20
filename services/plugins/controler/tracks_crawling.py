# python import
import datetime
from pymongo import DESCENDING
from spotipy.client import SpotifyException

# Core Services import
from core import toLog
from core.db import cursor
from config.settings import CAPPED_SIZE
from config.settings import CAPPED_NAME
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

    def fill_capped_collection(self):
        self.create_capped_collection()
        sort = [("followers", DESCENDING)]
        data = cursor.playlist.find().sort(sort).limit(CAPPED_SIZE)

        for doc in data:
            del doc['_id']
            cursor[CAPPED_NAME].insert(doc)

    def set_zero_capped_collection(self):
        cursor[CAPPED_NAME].remove({})

    def create_capped_collection(self):
        coll_names = cursor.collection_names()

        if CAPPED_NAME not in coll_names:
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

    @asynchronous
    def run(self, _continue=False):
        if not _continue:
            counter = CAPPED_SIZE
            self.create_capped_collection()
            self.fill_capped_collection()
        else:
            counter = cursor[CAPPED_NAME].count()

        for i in range(counter):
            data = cursor[CAPPED_NAME].find_one()


PlayListCrawl()
