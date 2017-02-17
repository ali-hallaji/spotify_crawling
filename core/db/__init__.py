from core.db.mongo_drivers import MongoConnection


def MongoCursor(db):
    return MongoConnection().getCursor(db)


if MongoConnection.exist:
    cursor = MongoCursor(MongoConnection.db_name)
