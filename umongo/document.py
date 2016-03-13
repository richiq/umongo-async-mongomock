from .data_proxy import DataProxy
from .exceptions import NotCreatedError
from .meta import MetaDocument


class Document(metaclass=MetaDocument):

    __slots__ = ('created', '_data')

    class Config:
        collection = None
        lazy_collection = None
        register_document = True

    def __init__(self, **kwargs):
        self.created = False
        self._data = DataProxy(self.schema, kwargs)

    @property
    def pk(self):
        return self._data._data.get('_id')

    @classmethod
    def build_from_mongo(cls, data, partial=False):
        doc = cls()
        doc.from_mongo(data, partial=partial)
        return doc

    def from_mongo(self, data, partial=False):
        # TODO: handle partial
        self._data.from_mongo(data, partial=partial)
        self.created = True

    def to_mongo(self, update=False):
        return self._data.to_mongo(update=update)

    def dump(self):
        return self._data.dump()

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

    def __getitem__(self, name):
        return self._data.get(name)

    def __delitem__(self, name):
        self._data.delete(name)

    def __setitem__(self, name, value):
        self._data.set(name, value)

    def __setattr__(self, name, value):
        if name in Document.__dict__:
            Document.__dict__[name].__set__(self, value)
        else:
            self._data.set(name, value)

    def __getattr__(self, name):
        return self._data.get(name)

    def __delattr__(self, name):
        self._data.delete(name)

    def __repr__(self):
        return '<object Document %s.%s(%s)>' % (
            self.__module__, self.__class__.__name__, self._data._data)
