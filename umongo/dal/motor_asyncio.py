from motor.motor_asyncio import AsyncIOMotorCollection

from ..abstract import AbstractDal
from ..data_proxy import DataProxy
from ..exceptions import NotCreatedError, UpdateError


class MotorAsyncIODal(AbstractDal):

    @staticmethod
    def is_compatible_with(collection):
        return isinstance(collection, AsyncIOMotorCollection)

    def reload(self, doc):
        ret = yield from doc.collection.find_one(doc.pk)
        if ret is None:
            raise NotCreatedError("Document doesn't exists in database")
        doc.data = DataProxy(doc.schema)
        doc.data.from_mongo(ret)

    def commit(self, doc, io_validate_all=False):
        doc.data.io_validate(validate_all=io_validate_all)
        payload = doc.data.to_mongo(update=doc.created)
        if doc.created:
            if payload:
                ret = yield from doc.collection.update(
                    {'_id': doc.data.get_by_mongo_name('_id')}, payload)
                if ret.get('nModified') != 1:
                    raise UpdateError(ret.raw_result)
        else:
            ret = yield from doc.collection.insert(payload)
            # TODO: check ret ?
            doc.data.set_by_mongo_name('_id', ret)
            doc.created = True
        doc.data.clear_modified()

    def delete(self, doc):
        raise NotImplementedError()

    def find_one(self, doc_cls, *args, **kwargs):
        ret = yield from doc_cls.collection.find_one(*args, **kwargs)
        if ret is not None:
            ret = doc_cls.build_from_mongo(ret)
        return ret

    def find(self, doc_cls, *args, **kwargs):
        from ..cursor import Cursor
        raw_cursor = yield from doc_cls.collection.find(*args, **kwargs)
        return Cursor(doc_cls, raw_cursor)
