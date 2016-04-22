from .pymongo import PyMongoDal
from mongomock.database import Database


# Mongomock aims at working like pymongo
class MongoMockDal(PyMongoDal):

    @staticmethod
    def is_compatible_with(db):
        return isinstance(db, Database)
