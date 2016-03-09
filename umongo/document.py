from .data_proxy import DataProxy
from .abstract import BaseWrappedData
from .exceptions import UpdateError, NotCreatedError
from .meta import MetaDocument


class Document(BaseWrappedData, metaclass=MetaDocument):

    class Config:
        collection = None
        lazy_collection = None
        register_document = True

    def __init__(self, **kwargs):
        self.created = False
        self.data = DataProxy(self.schema, kwargs)

    @property
    def pk(self):
        return self.data._data.get('_id')

    @property
    def name(self):
        return self.__name__

    @classmethod
    def build_from_mongo(cls, data, partial=False):
        doc = cls()
        doc.from_mongo(data, partial=partial)
        return doc

    def from_mongo(self, data, partial=False):
        # TODO: handle partial
        self.data.from_mongo(data, partial=partial)
        self.created = True

    def to_mongo(self, update=False):
        return self.data.to_mongo(update=update)

    def dump(self):
        return self.data.dump()

    def reload(self):
        if not self.created:
            raise NotCreatedError('Cannot reload a document that'
                                  ' has not been committed yet')
        ret = self.collection.find_one(self.pk)
        if ret is None:
            raise NotCreatedError("Document doesn't exists in database")
        self.data = DataProxy(self.schema)
        self.data.from_mongo(ret)

    def commit(self, io_validate_all=False):
        # TODO: implement in driver
        self.data.io_validate(validate_all=io_validate_all)
        payload = self.data.to_mongo(update=self.created)
        if self.created:
            if payload:
                ret = self.collection.update_one(
                    {'_id': self.data.get_by_mongo_name('_id')}, payload)
                if ret.modified_count != 1:
                    raise UpdateError(ret.raw_result)
        else:
            ret = self.collection.insert_one(payload)
            # TODO: check ret ?
            self.data.set_by_mongo_name('_id', ret.inserted_id)
            self.created = True
        self.data.clear_modified()
        return self

    @property
    def collection(self):
        # Cannot implicitly access to the class's property
        return type(self).collection

    @classmethod
    def find_one(cls, *args, **kwargs):
        ret = cls.collection.find_one(*args, **kwargs)
        if ret is not None:
            ret = cls.build_from_mongo(ret)
        return ret

    @classmethod
    def find(cls, *args, **kwargs):
        from .cursor import Cursor
        cursor = cls.collection.find(*args, **kwargs)
        return Cursor(cls, cursor)
