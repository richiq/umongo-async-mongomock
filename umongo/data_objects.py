from bson import DBRef

from .abstract import BaseDataObject
from .data_proxy import DataProxy
from .meta import MetaEmbeddedDocument


__all__ = ('EmbeddedDocument', 'List', 'Reference')


class EmbeddedDocument(BaseDataObject, metaclass=MetaEmbeddedDocument):

    __slots__ = ('_callback', '_data', '_modified')

    def is_modified(self):
        return self._modified

    def set_modified(self):
        self._modified = True

    def clear_modified(self):
        self._modified = False
        self._data.clear_modified()

    def __init__(self, **kwargs):
        schema = self.Schema()
        self._modified = False
        self._data = DataProxy(schema, kwargs)

    def from_mongo(self, data):
        self._data.from_mongo(data)

    def to_mongo(self, update=False):
        return self._data.to_mongo(update=update)

    def dump(self):
        return self._data.dump()

    def __getitem__(self, name):
        return self._data.get(name)

    def __delitem__(self, name):
        self.set_modified()
        self._data.delete(name)

    def __setitem__(self, name, value):
        self.set_modified()
        self._data.set(name, value)

    def __setattr__(self, name, value):
        if name in EmbeddedDocument.__dict__:
            EmbeddedDocument.__dict__[name].__set__(self, value)
        else:
            self.set_modified()
            self._data.set(name, value)

    def __getattr__(self, name):
        return self._data.get(name)

    def __delattr__(self, name):
        self.set_modified()
        self._data.delete(name)

    def __eq__(self, other):
        if isinstance(other, dict):
            return self._data == other
        else:
            return self._data == other._data

    def __repr__(self):
        return '<object EmbeddedDocument %s.%s(%s)>' % (
            self.__module__, self.__class__.__name__, self._data._data)


class List(BaseDataObject, list):

    def __init__(self, container_field, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.container_field = container_field

    def append(self, obj):
        obj = self.container_field.deserialize(obj)
        ret = super().append(obj)
        self.set_modified()
        return ret

    def pop(self, *args, **kwargs):
        ret = super().pop(*args, **kwargs)
        self.set_modified()
        return ret

    def clear(self, *args, **kwargs):
        ret = super().clear(*args, **kwargs)
        self.set_modified()
        return ret

    def remove(self, *args, **kwargs):
        ret = super().remove(*args, **kwargs)
        self.set_modified()
        return ret

    def reverse(self, *args, **kwargs):
        ret = super().reverse(*args, **kwargs)
        self.set_modified()
        return ret

    def sort(self, *args, **kwargs):
        ret = super().sort(*args, **kwargs)
        self.set_modified()
        return ret

    def extend(self, iterable):
        iterable = [self.container_field.deserialize(obj) for obj in iterable]
        ret = super().extend(iterable)
        self.set_modified()
        return ret

    def __repr__(self):
        return '<object %s.%s(%s)>' % (
            self.__module__, self.__class__.__name__, list(self))


class Dict(BaseDataObject, dict):
    pass


class Reference:

    def __init__(self, document_cls, pk):
        self.document_cls = document_cls
        self.pk = pk
        self._document = None

    def io_fetch(self, no_data=False):
        raise NotImplementedError

    def __repr__(self):
        return '<object Reference %s.%s(document=%s, id=%s)>' % (
            self.__module__, self.__class__.__name__, self.pk, self.document_cls.__name__)

    def __eq__(self, other):
        if isinstance(other, self.document_cls):
            return other.pk == self.pk
        elif isinstance(other, Reference):
            return self.pk == other.pk and self.document_cls == other.document_cls
        elif isinstance(other, DBRef):
            return self.pk == other.id and self.document_cls.collection.name == other.collection
        return NotImplemented
