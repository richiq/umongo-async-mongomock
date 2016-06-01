from .document import Implementation, MetaTemplate, MetaImplementation
from .data_objects import BaseDataObject
from .data_proxy import DataProxy


class EmbeddedDocumentOpts:
    """
    Configuration for an :class:`umongo.embedded_document.EmbeddedDocument`.
    """

    def __repr__(self):
        return ('<{ClassName}(instance={self.instance}, template={self.template})>'
                .format(ClassName=self.__class__.__name__, self=self))

    def __init__(self, instance, template):
        self.instance = instance
        self.template = template


class EmbeddedDocumentTemplate(metaclass=MetaTemplate):
    pass


EmbeddedDocument = EmbeddedDocumentTemplate
"Shortcut to EmbeddedDocumentTemplate"


class EmbeddedDocumentImplementation(Implementation, BaseDataObject, metaclass=MetaImplementation):

    __slots__ = ('_callback', '_data', '_modified')
    opts = EmbeddedDocumentOpts(None, EmbeddedDocumentTemplate)

    def __init__(self, **kwargs):
        schema = self.Schema()
        self._modified = False
        self._data = DataProxy(schema, kwargs)

    def __repr__(self):
        return '<object EmbeddedDocument %s.%s(%s)>' % (
            self.__module__, self.__class__.__name__, self._data._data)

    def __eq__(self, other):
        if isinstance(other, dict):
            return self._data == other
        else:
            return self._data == other._data

    def is_modified(self):
        return self._modified

    def set_modified(self):
        self._modified = True

    def clear_modified(self):
        self._modified = False
        self._data.clear_modified()

    def from_mongo(self, data):
        self._data.from_mongo(data)

    def to_mongo(self, update=False):
        return self._data.to_mongo(update=update)

    def dump(self):
        return self._data.dump()

    # Data-proxy accessor shortcuts

    def __getitem__(self, name):
        return self._data.get(name)

    def __delitem__(self, name):
        self.set_modified()
        self._data.delete(name)

    def __setitem__(self, name, value):
        self.set_modified()
        self._data.set(name, value)

    def __setattr__(self, name, value):
        if name in EmbeddedDocumentImplementation.__dict__:
            EmbeddedDocumentImplementation.__dict__[name].__set__(self, value)
        else:
            self.set_modified()
            self._data.set(name, value)

    def __getattr__(self, name):
        return self._data.get(name)

    def __delattr__(self, name):
        self.set_modified()
        self._data.delete(name)
