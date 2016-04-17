from .pymongo import PyMongoDal
from mongomock.collection import Collection


# Mongomock aims at working like pymongo
class MongoMockDal(PyMongoDal):

    @staticmethod
    def is_compatible_with(collection):
        return isinstance(collection, Collection)
