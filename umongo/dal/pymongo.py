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

    def reload(self, doc):
        ret = doc.collection.find_one(doc.pk)
        if ret is None:
            raise NotCreatedError("Document doesn't exists in database")
        doc._data = DataProxy(doc.schema)
        doc._data.from_mongo(ret)

    def commit(self, doc, io_validate_all=False):
        doc._data.io_validate(validate_all=io_validate_all)
        payload = doc._data.to_mongo(update=doc.created)
        if doc.created:
            if payload:
                ret = doc.collection.update_one(
                    {'_id': doc._data.get_by_mongo_name('_id')}, payload)
                if ret.modified_count != 1:
                    raise UpdateError(ret.raw_result)
        else:
            ret = doc.collection.insert_one(payload)
            # TODO: check ret ?
            doc._data.set_by_mongo_name('_id', ret.inserted_id)
            doc.created = True
        doc._data.clear_modified()

    def delete(self, doc):
        ret = doc.collection.delete_one({'_id': doc.pk})
        if ret.deleted_count != 1:
            raise DeleteError(ret.raw_result)

    def find_one(self, doc_cls, *args, **kwargs):
        ret = doc_cls.collection.find_one(*args, **kwargs)
        if ret is not None:
            ret = doc_cls.build_from_mongo(ret)
        return ret

    def find(self, doc_cls, *args, **kwargs):
        raw_cursor = doc_cls.collection.find(*args, **kwargs)
        return WrappedCursor(doc_cls, raw_cursor)
