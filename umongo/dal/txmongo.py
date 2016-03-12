from txmongo.collection import Collection
from twisted.internet.defer import inlineCallbacks

from ..abstract import AbstractCursor, AbstractDal
from ..data_proxy import DataProxy
from ..exceptions import NotCreatedError, UpdateError


class TxCursor(AbstractCursor):

    def __init__(self, document_cls, cursor, *args, **kwargs):
        self._next_index = 0
        self.raw_cursor = cursor
        self.document_cls = document_cls
        self._total = len(cursor)
        self._total_with_limit_and_skip = len(cursor)

    def __next__(self):
        if self._next_index >= self._total_with_limit_and_skip:
            raise StopIteration
        else:
            val = self.raw_cursor[self._next_index]
            self._next_index += 1
            return val

    def __iter__(self):
        for elem in self.raw_cursor:
            yield self.document_cls.build_from_mongo(elem)

    def count(self, with_limit_and_skip=False):
        if with_limit_and_skip:
            return self._total
        else:
            return 10  # !!!


class TxMongoDal(AbstractDal):

    @staticmethod
    def is_compatible_with(collection):
        return isinstance(collection, Collection)

    @inlineCallbacks
    def reload(self, doc):
        ret = yield doc.collection.find_one(doc.pk)
        if ret is None:
            raise NotCreatedError("Document doesn't exists in database")
        doc.data = DataProxy(doc.schema)
        doc.data.from_mongo(ret)

    @inlineCallbacks
    def commit(self, doc, io_validate_all=False):
        doc.data.io_validate(validate_all=io_validate_all)
        payload = doc.data.to_mongo(update=doc.created)
        if doc.created:
            if payload:
                ret = yield doc.collection.update_one(
                    {'_id': doc.data.get_by_mongo_name('_id')}, payload)
                if ret.modified_count != 1:
                    raise UpdateError(ret.raw_result)
        else:
            ret = yield doc.collection.insert_one(payload)
            # TODO: check ret ?
            doc.data.set_by_mongo_name('_id', ret.inserted_id)
            doc.created = True
        doc.data.clear_modified()

    def delete(self, doc):
        raise NotImplementedError()

    @inlineCallbacks
    def find_one(self, doc_cls, *args, **kwargs):
        ret = yield doc_cls.collection.find_one(*args, **kwargs)
        if ret is not None:
            ret = doc_cls.build_from_mongo(ret)
        return ret

    @inlineCallbacks
    def find(self, doc_cls, *args, **kwargs):
        raw_cursor = yield doc_cls.collection.find(*args, **kwargs)
        return TxCursor(doc_cls, raw_cursor)
