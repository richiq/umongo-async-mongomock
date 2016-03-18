from txmongo.collection import Collection
from twisted.internet.defer import inlineCallbacks

from ..abstract import AbstractDal
from ..data_proxy import DataProxy
from ..exceptions import NotCreatedError, UpdateError, DeleteError


class TxMongoDal(AbstractDal):

    @staticmethod
    def is_compatible_with(collection):
        return isinstance(collection, Collection)

    @inlineCallbacks
    def reload(self, doc):
        ret = yield doc.collection.find_one(doc.pk)
        if ret is None:
            raise NotCreatedError("Document doesn't exists in database")
        doc._data = DataProxy(doc.schema)
        doc._data.from_mongo(ret)

    @inlineCallbacks
    def commit(self, doc, io_validate_all=False):
        doc._data.io_validate(validate_all=io_validate_all)
        payload = doc._data.to_mongo(update=doc.created)
        if doc.created:
            if payload:
                ret = yield doc.collection.update_one(
                    {'_id': doc._data.get_by_mongo_name('_id')}, payload)
                if ret.modified_count != 1:
                    raise UpdateError(ret.raw_result)
        else:
            ret = yield doc.collection.insert_one(payload)
            # TODO: check ret ?
            doc._data.set_by_mongo_name('_id', ret.inserted_id)
            doc.created = True
        doc._data.clear_modified()

    @inlineCallbacks
    def delete(self, doc):
        ret = yield doc.collection.delete_one({'_id': doc.pk})
        if ret.deleted_count != 1:
            raise DeleteError(ret.raw_result)

    @inlineCallbacks
    def find_one(self, doc_cls, *args, **kwargs):
        ret = yield doc_cls.collection.find_one(*args, **kwargs)
        if ret is not None:
            ret = doc_cls.build_from_mongo(ret)
        return ret

    @inlineCallbacks
    def find(self, doc_cls, *args, **kwargs):
        raw_cursor_or_list = yield doc_cls.collection.find(*args, **kwargs)
        if isinstance(raw_cursor_or_list, tuple):

            def wrap_raw_results(result):
                cursor = result[1]
                if cursor is not None:
                    cursor.addCallback(wrap_raw_results)
                return ([doc_cls.build_from_mongo(e) for e in result[0]], cursor)

            return wrap_raw_results(raw_cursor_or_list)
        else:
            return [doc_cls.build_from_mongo(e) for e in raw_cursor_or_list]
