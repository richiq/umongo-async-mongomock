from .data_proxy import DataProxy
from .abstract import BaseWrappedData
from .exceptions import NotCreatedError
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

    @property
    def collection(self):
        # Cannot implicitly access to the class's property
        return type(self).collection

    @property
    def driver(self):
        # Cannot implicitly access to the class's property
        return type(self).driver

    def reload(self):
        if not self.created:
            raise NotCreatedError('Cannot reload a document that'
                                  ' has not been committed yet')
        return self.driver.reload(self)

    def commit(self, io_validate_all=False):
        return self.driver.commit(self, io_validate_all=False)

    def delete(self):
        return self.driver.delete(self)

    @classmethod
    def find_one(cls, *args, **kwargs):
        return cls.driver.find_one(cls, *args, **kwargs)

    @classmethod
    def find(cls, *args, **kwargs):
        return cls.driver.find(cls, *args, **kwargs)
