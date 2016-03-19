from pymongo.collection import Collection
from pymongo.cursor import Cursor

from ..abstract import AbstractDal
from ..data_proxy import DataProxy
from ..exceptions import NotCreatedError, UpdateError, DeleteError


class WrappedCursor(Cursor):

    __slots__ = ('raw_cursor', 'document_cls')

    def __init__(self, document_cls, cursor, *args, **kwargs):
        # Such a cunning plan my lord !
        # We inherit from Cursor but don't call it __init__ because
        # we act as a proxy to the underlying raw_cursor
        WrappedCursor.raw_cursor.__set__(self, cursor)
        WrappedCursor.document_cls.__set__(self, document_cls)

    def __getattr__(self, name):
        return getattr(self.raw_cursor, name)

    def __setattr__(self, name, value):
        return setattr(self.raw_cursor, name, value)

    def __next__(self):
        elem = next(self.raw_cursor)
        return self.document_cls.build_from_mongo(elem)

    def __iter__(self):
        for elem in self.raw_cursor:
            yield self.document_cls.build_from_mongo(elem)


class PyMongoDal(AbstractDal):

    @staticmethod
    def is_compatible_with(collection):
        return isinstance(collection, Collection)

    def reload(self):
        ret = self.collection.find_one(self.pk)
        if ret is None:
            raise NotCreatedError("Document doesn't exists in database")
        self._data = DataProxy(self.schema)
        self._data.from_mongo(ret)

    def commit(self, io_validate_all=False):
        self._data.io_validate(validate_all=io_validate_all)
        payload = self._data.to_mongo(update=self.created)
        if self.created:
            if payload:
                ret = self.collection.update_one(
                    {'_id': self._data.get_by_mongo_name('_id')}, payload)
                if ret.modified_count != 1:
                    raise UpdateError(ret.raw_result)
        else:
            ret = self.collection.insert_one(payload)
            # TODO: check ret ?
            self._data.set_by_mongo_name('_id', ret.inserted_id)
            self.created = True
        self._data.clear_modified()

    def delete(self):
        ret = self.collection.delete_one({'_id': self.pk})
        if ret.deleted_count != 1:
            raise DeleteError(ret.raw_result)

    @classmethod
    def find_one(cls, *args, **kwargs):
        ret = cls.collection.find_one(*args, **kwargs)
        if ret is not None:
            ret = cls.build_from_mongo(ret)
        return ret

    @classmethod
    def find(cls, *args, **kwargs):
        raw_cursor = cls.collection.find(*args, **kwargs)
        return WrappedCursor(cls, raw_cursor)
