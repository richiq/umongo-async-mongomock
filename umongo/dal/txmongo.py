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
    def reload(self):
        ret = yield self.collection.find_one(self.pk)
        if ret is None:
            raise NotCreatedError("Document doesn't exists in database")
        self._data = DataProxy(self.schema)
        self._data.from_mongo(ret)

    @inlineCallbacks
    def commit(self, io_validate_all=False):
        self._data.io_validate(validate_all=io_validate_all)
        payload = self._data.to_mongo(update=self.created)
        if self.created:
            if payload:
                ret = yield self.collection.update_one(
                    {'_id': self._data.get_by_mongo_name('_id')}, payload)
                if ret.modified_count != 1:
                    raise UpdateError(ret.raw_result)
        else:
            ret = yield self.collection.insert_one(payload)
            # TODO: check ret ?
            self._data.set_by_mongo_name('_id', ret.inserted_id)
            self.created = True
        self._data.clear_modified()

    @inlineCallbacks
    def delete(self):
        ret = yield self.collection.delete_one({'_id': self.pk})
        if ret.deleted_count != 1:
            raise DeleteError(ret.raw_result)

    @classmethod
    @inlineCallbacks
    def find_one(cls, *args, **kwargs):
        ret = yield cls.collection.find_one(*args, **kwargs)
        if ret is not None:
            ret = cls.build_from_mongo(ret)
        return ret

    @classmethod
    @inlineCallbacks
    def find(cls, *args, **kwargs):
        raw_cursor_or_list = yield cls.collection.find(*args, **kwargs)
        if isinstance(raw_cursor_or_list, tuple):

            def wrap_raw_results(result):
                cursor = result[1]
                if cursor is not None:
                    cursor.addCallback(wrap_raw_results)
                return ([cls.build_from_mongo(e) for e in result[0]], cursor)

            return wrap_raw_results(raw_cursor_or_list)
        else:
            return [cls.build_from_mongo(e) for e in raw_cursor_or_list]
