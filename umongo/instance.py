from .exceptions import (
    NotRegisteredDocumentError, AlreadyRegisteredDocumentError, NoDBDefinedError)
from .document import DocumentImplementation


class BaseInstance:
    """
    Base class for instance.

    Instances aims at collecting and implementing document templates::

        # Doc is a template, cannot use it for the moment
        class Doc(Document):
            pass

        instance = Instance()
        # doc_cls is the instance's implementation of Doc
        doc_cls = instance.register(Doc)
        # Implementations are registered as attribute into the instance
        instance.Doc is doc_cls
        # Now we can work with the implementations
        doc_cls.find()

    """

    BUILDER_CLS = None

    def __init__(self, doc_templates=()):
        assert self.BUILDER_CLS, 'BUILDER_CLS must be defined.'
        self.builder = self.BUILDER_CLS(self)
        self._doc_lookup = {}
        for doc_template in doc_templates:
            self.register(doc_template)

    @property
    def db(self):
        raise NotImplementedError

    def retrieve_document(self, name_or_template):
        """
        Retrieve a :class:`umongo.DocumentImplementation` registered into this
        instance from it name or it template class (i.e. :class:`umongo.Document`).
        """
        if not isinstance(name_or_template, str):
            name_or_template = name_or_template.__name__
        if name_or_template not in self._doc_lookup:
            raise NotRegisteredDocumentError(
                'Unknown document class `%s`' % name_or_template)
        return self._doc_lookup[name_or_template]

    def register(self, doc_template):
        """
        Generate a :class:`umongo.DocumentImplementation` from the given
        :class:`umongo.Document` template for this instance.

        :return: The :class:`umongo.DocumentImplementation` generated

        .. note::
            This method can be used as a decorator. This is useful when you
            only have a single instance to work with to directly use the
            class you defined::

                @instance.register
                class Doc:
                    pass

                Doc.find()

        """
        if issubclass(doc_template, DocumentImplementation):
            doc_template = doc_template.opts.template
        doc_cls = self.builder.build_from_template(doc_template)
        if hasattr(self, doc_cls.__name__):
            raise AlreadyRegisteredDocumentError(
                'Document `%s` already registered' % doc_cls.__name__)
        setattr(self, doc_cls.__name__, doc_cls)
        self._doc_lookup[doc_cls.__name__] = doc_cls
        return doc_cls


class Instance(BaseInstance):
    """
    Automatically configured instance according to the type of
    the provided database.
    """

    def __init__(self, db, doc_templates=()):
        self._db = db
        # Dynamically find a builder compatible with the db
        from .frameworks import find_builder_from_db
        self.BUILDER_CLS = find_builder_from_db(db)
        super().__init__(doc_templates=doc_templates)

    @property
    def db(self):
        return self._db


class LazyLoaderInstance(BaseInstance):
    """
    Base class for instance with database lazy loading

    .. note::
        This class should not be used directly but instead overloaded.
        See :class:`umongo.PyMongoInstance` for example.

    """

    def __init__(self, doc_templates=()):
        self._db = None
        super().__init__(doc_templates=doc_templates)

    @property
    def db(self):
        if not self._db:
            raise NoDBDefinedError('init must be called to define a db')
        return self._db

    def init(self, db):
        """
        Set the database to use whithin this instance.

        .. note::
            The document registered in the instance cannot be used
            before this function is called.
        """
        assert self.BUILDER_CLS.is_compatible_with(db)
        self._db = db
