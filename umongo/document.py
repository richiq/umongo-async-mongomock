from .data_proxy import DataProxy
from .exceptions import NotCreatedError
from .meta import MetaDocument
from .data_objects import Reference

from bson import DBRef


class Document(metaclass=MetaDocument):

    __slots__ = ('created', '_data')

    class Config:
        collection = None
        lazy_collection = None
        dal = None
        register_document = True

    def __init__(self, **kwargs):
        super().__init__()
        self.created = False
        self._data = DataProxy(self.schema, data=kwargs if kwargs else None)

    def __repr__(self):
        return '<object Document %s.%s(%s)>' % (
            self.__module__, self.__class__.__name__, self._data._data)

    def __eq__(self, other):
        if self.pk is None:
            return self is other
        elif isinstance(other, self.__class__) and other.pk is not None:
            return self.pk == other.pk
        elif isinstance(other, DBRef):
            return other.collection == self.collection.name and other.id == self.pk
        elif isinstance(other, Reference):
            return isinstance(self, other.document_cls) and self.pk == other.pk
        return NotImplemented

    @property
    def pk(self):
        """Return the document's primary key (i.e. `_id` in mongo notation) or
        None if not available yet
        """
        return self._data.get_by_mongo_name('_id')

    @property
    def dbref(self):
        """Return a pymongo DBRef instance related to the document
        """
        if not self.created:
            raise NotCreatedError('Must create the document before'
                                  ' having access to DBRef')
        return DBRef(collection=self.collection.name, id=self.pk)

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
        if update and not self.created:
            raise NotCreatedError('Must create the document before'
                                  ' using update')
        return self._data.to_mongo(update=update)

    def dump(self):
        return self._data.dump()

    def clear_modified(self):
        self._data.clear_modified()

    @property
    def collection(self):
        # Cannot implicitly access to the class's property
        return type(self).collection

    # Data-proxy accessor shortcuts

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
