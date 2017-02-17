import urllib

from pymongo import MongoClient
from pymongo import ReadPreference

from config import settings
from config.settings import EXIST_DB
from config.settings import DB_NAME
from core.patterns.class_singleton import Singleton


@Singleton
class MongoConnection(object):
    __db = None
    db_name = DB_NAME
    exist = EXIST_DB

    @classmethod
    def get_connection(cls):
        """Singleton method for running Mongo instance"""
        if cls.__db is None:
            user = getattr(settings, 'MONGO_USER', None)
            password = getattr(settings, 'MONGO_PASSWORD', None)

            if user and password:
                password = urllib.quote_plus(password)
                auth = '{0}:{1}@'.format(user, password)
            else:
                auth = ''

            if getattr(settings, 'BALANCING', None):
                address = settings.MONGO_LOAD_BALANCE
            else:
                address = '{0}:{1}'.format(
                    settings.MONGO_HOST,
                    settings.MONGO_PORT
                )

            connection_string = 'mongodb://{}{}'.format(auth, address)

            cls.__db = MongoClient(
                connection_string,
                serverSelectionTimeoutMS=6000,
                maxPoolSize=None,
                read_preference=ReadPreference.NEAREST,
                connect=False
            )
        return cls.__db

    def __init__(self):
        self.get_connection()

    def getCursor(self, db):
        return self.__db[db]
