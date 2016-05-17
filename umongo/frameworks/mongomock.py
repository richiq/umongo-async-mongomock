from .pymongo import PyMongoBuilder
from mongomock.database import Database


# Mongomock aims at working like pymongo
class MongoMockBuilder(PyMongoBuilder):

    @staticmethod
    def is_compatible_with(db):
        return isinstance(db, Database)
