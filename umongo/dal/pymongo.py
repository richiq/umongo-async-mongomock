from pymongo.collection import Collection

from ..abstract import AbstractDal
from ..data_proxy import DataProxy
from ..exceptions import NotCreatedError, UpdateError, DeleteError


class PyMongoDal(AbstractDal):

    @staticmethod
    def is_compatible_with(collection):
        return isinstance(collection, Collection)

    def reload(self, doc):
        ret = doc.collection.find_one(doc.pk)
        if ret is None:
            raise NotCreatedError("Document doesn't exists in database")
        doc.data = DataProxy(doc.schema)
        doc.data.from_mongo(ret)

    def commit(self, doc, io_validate_all=False):
        doc.data.io_validate(validate_all=io_validate_all)
        payload = doc.data.to_mongo(update=doc.created)
        if doc.created:
            if payload:
                ret = doc.collection.update_one(
                    {'_id': doc.data.get_by_mongo_name('_id')}, payload)
                if ret.modified_count != 1:
                    raise UpdateError(ret.raw_result)
        else:
            ret = doc.collection.insert_one(payload)
            # TODO: check ret ?
            doc.data.set_by_mongo_name('_id', ret.inserted_id)
            doc.created = True
        doc.data.clear_modified()

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
        from ..cursor import Cursor
        raw_cursor = doc_cls.collection.find(*args, **kwargs)
        return Cursor(doc_cls, raw_cursor)
