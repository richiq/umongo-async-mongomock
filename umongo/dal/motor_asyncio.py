from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorCursor
from asyncio import Future

from ..abstract import AbstractDal
from ..data_proxy import DataProxy
from ..exceptions import NotCreatedError, UpdateError


class WrappedCursor(AsyncIOMotorCursor):

    __slots__ = ('raw_cursor', 'document_cls')

    def __init__(self, document_cls, cursor):
        # Such a cunning plan my lord !
        # We inherit from Cursor but don't call it __init__ because
        # we act as a proxy to the underlying raw_cursor
        WrappedCursor.raw_cursor.__set__(self, cursor)
        WrappedCursor.document_cls.__set__(self, document_cls)

    def __getattr__(self, name):
        return getattr(self.raw_cursor, name)

    def __setattr__(self, name, value):
        return setattr(self.raw_cursor, name, value)

    def clone(self):
        return WrappedCursor(self.document_cls, self.raw_cursor.clone())

    def next_object(self):
        raw = self.raw_cursor.next_object()
        return self.document_cls.build_from_mongo(raw)

    def each(self, callback):
        def wrapped_callback(result, error):
            if not error and result is not None:
                result = self.document_cls.build_from_mongo(result)
            return callback(result, error)
        return self.raw_cursor.each(wrapped_callback)

    def to_list(self, length, callback=None):
        raw_future = self.raw_cursor.to_list(length, callback=callback)
        cooked_future = Future()
        builder = self.document_cls.build_from_mongo

        def on_raw_done(fut):
            cooked_future.set_result([builder(e) for e in fut.result()])

        raw_future.add_done_callback(on_raw_done)
        return cooked_future


class MotorAsyncIODal(AbstractDal):

    @staticmethod
    def is_compatible_with(collection):
        return isinstance(collection, AsyncIOMotorCollection)

    def reload(self, doc):
        ret = yield from doc.collection.find_one(doc.pk)
        if ret is None:
            raise NotCreatedError("Document doesn't exists in database")
        doc._data = DataProxy(doc.schema)
        doc._data.from_mongo(ret)

    def commit(self, doc, io_validate_all=False):
        doc._data.io_validate(validate_all=io_validate_all)
        payload = doc._data.to_mongo(update=doc.created)
        if doc.created:
            if payload:
                ret = yield from doc.collection.update(
                    {'_id': doc._data.get_by_mongo_name('_id')}, payload)
                if ret.get('nModified') != 1:
                    raise UpdateError(ret.raw_result)
        else:
            ret = yield from doc.collection.insert(payload)
            # TODO: check ret ?
            doc._data.set_by_mongo_name('_id', ret)
            doc.created = True
        doc._data.clear_modified()

    def delete(self, doc):
        raise NotImplementedError()

    def find_one(self, doc_cls, *args, **kwargs):
        ret = yield from doc_cls.collection.find_one(*args, **kwargs)
        if ret is not None:
            ret = doc_cls.build_from_mongo(ret)
        return ret

    def find(self, doc_cls, *args, **kwargs):
        return WrappedCursor(doc_cls, doc_cls.collection.find(*args, **kwargs))
