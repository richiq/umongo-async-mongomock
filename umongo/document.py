from bson import DBRef

from .data_proxy import DataProxy
from .exceptions import (NotCreatedError, NoDBDefinedError,
                         AbstractDocumentError, DocumentDefinitionError)
from .schema import Schema


class DocumentOpts:

    def __repr__(self):
        return ('<{ClassName}('
                'instance={self.instance}, '
                'abstract={self.abstract}, '
                'allow_inheritance={self.allow_inheritance}, '
                'collection_name={self.collection_name}, '
                'is_child={self.is_child}, '
                'base_schema_cls={self.base_schema_cls}, '
                'indexes={self.indexes}, '
                'children={self.children})>'
                .format(ClassName=self.__class__.__name__, self=self))

    def __init__(self, instance, collection_name=None, abstract=False,
                 allow_inheritance=None, base_schema_cls=Schema, indexes=None,
                 is_child=False, children=None):
        self.instance = instance
        self.collection_name = collection_name if not abstract else None
        self.abstract = abstract
        self.allow_inheritance = abstract if allow_inheritance is None else allow_inheritance
        self.base_schema_cls = base_schema_cls
        self.indexes = indexes or []
        self.is_child = is_child
        self.children = set(children) if children else set()
        if self.abstract and not self.allow_inheritance:
            raise DocumentDefinitionError("Abstract document cannot disable inheritance")


class MetaDocument(type):

    @property
    def collection(cls):
        if cls.opts.abstract:
            raise NoDBDefinedError('Abstract document has no collection')
        if not cls.opts.instance.db:
            raise NoDBDefinedError('Instance must be initialized first')
        return cls.opts.instance.db[cls.opts.collection_name]


class Document(metaclass=MetaDocument):
    """
    This class is used to mark a document definition.

    However
    """

    __slots__ = ()

    @property
    def collection(self):
        """
        Return the collection used by this document class
        """
        # Cannot implicitly access to the class's property
        return type(self).collection


class DocumentImplementation(Document):
    """
    """

    __slots__ = ('created', '_data')

    opts = DocumentOpts(None, abstract=True, allow_inheritance=True)

    def __init__(self, **kwargs):
        if self.opts.abstract:
            raise AbstractDocumentError("Cannot instantiate an abstract Document")
        self.created = False
        "Return True if the document has been commited to database"  # created's docstring
        self._data = DataProxy(self.schema, data=kwargs if kwargs else None)

    def __repr__(self):
        return '<object Document %s.%s(%s)>' % (
            self.__module__, self.__class__.__name__, self._data._data)

    def __eq__(self, other):
        from .data_objects import Reference
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
        """
        Return the document's primary key (i.e. ``_id`` in mongo notation) or
        None if not available yet

        .. warning:: Use ``created`` field instead to test if the document
                     has already been commited to database given ``_id``
                     field could be generated before insertion
        """
        return self._data.get_by_mongo_name('_id')

    @property
    def dbref(self):
        """
        Return a pymongo DBRef instance related to the document
        """
        if not self.created:
            raise NotCreatedError('Must create the document before'
                                  ' having access to DBRef')
        return DBRef(collection=self.collection.name, id=self.pk)

    @classmethod
    def build_from_mongo(cls, data, partial=False, use_cls=False):
        """
        Create a document instance from MongoDB data

        :param data: data as retrieved from MongoDB
        :param use_cls: if the data contains a ``_cls`` field,
            use it determine the Document class to instanciate
        """
        # If a _cls is specified, we have to use this document class
        if use_cls and '_cls' in data:
            cls = cls.opts.instance.retrieve_document(data['_cls'])
        doc = cls()
        doc.from_mongo(data, partial=partial)
        return doc

    def from_mongo(self, data, partial=False):
        """
        Update the document with the MongoDB data

        :param data: data as retrieved from MongoDB
        """
        # TODO: handle partial
        self._data.from_mongo(data, partial=partial)
        self.created = True

    def to_mongo(self, update=False):
        """
        Return the document as a dict compatible with MongoDB driver

        :param update: if True the return dict should be used as an
                       update payload instead of containing the entire document
        """
        if update and not self.created:
            raise NotCreatedError('Must create the document before'
                                  ' using update')
        return self._data.to_mongo(update=update)

    def update(self, data, schema=None):
        """
        Update the document with the given data

        :param schema: use this schema for the load instead of the default one
        """
        return self._data.update(data, schema=schema)

    def dump(self, schema=None):
        """
        Dump the document

        :param schema: use this schema for the dump instead of the default one
        :return: a JSON compatible ``dict`` representing the document
        """
        return self._data.dump(schema=schema)

    def clear_modified(self):
        """
        Reset the list of document's modified items
        """
        self._data.clear_modified()

    # Data-proxy accessor shortcuts

    def __getitem__(self, name):
        return self._data.get(name)

    def __delitem__(self, name):
        self._data.delete(name)

    def __setitem__(self, name, value):
        self._data.set(name, value)

    def __setattr__(self, name, value):
        if name in DocumentImplementation.__dict__:
            DocumentImplementation.__dict__[name].__set__(self, value)
        else:
            self._data.set(name, value, to_raise=AttributeError)

    def __getattr__(self, name):
        return self._data.get(name, to_raise=AttributeError)

    def __delattr__(self, name):
        self._data.delete(name, to_raise=AttributeError)
