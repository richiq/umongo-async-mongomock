from marshmallow.fields import Field

from .registerer import register_document
from .exceptions import NoCollectionDefinedError, DocumentDefinitionError
from .schema import Schema, EmbeddedSchema
from .abstract import AbstractDal
from .indexes import parse_index


def _is_child(bases):
    """Find if the given inheritance leeds to a child document (i.e.
    a document that shares the same collection with a parent)
    """
    return bool([b for b in bases if not b.opts.abstract])


def _collect_fields(nmspc):
    """Split dict between fields and non-fields elements"""
    schema_nmspc = {}
    doc_nmspc = {}
    for key, item in nmspc.items():
        if isinstance(item, Field):
            schema_nmspc[key] = item
        else:
            doc_nmspc[key] = item
    return doc_nmspc, schema_nmspc


def _collect_indexes(nmspc, bases):
    """Retrieve all indexes (custom defined in meta class, by inheritances
    and unique attribut in fields)
    """
    meta = nmspc.get('Meta')
    indexes = []
    is_child = _is_child(bases)

    # First collect parent indexes (including inherited field's unique indexes)
    for base in bases:
        indexes += base.opts.indexes

    # Then get our own custom indexes
    if is_child:
        custom_indexes = [parse_index(x, base_compound_field='_cls')
                   for x in getattr(meta, 'indexes', ())]
    else:
        custom_indexes = [parse_index(x) for x in getattr(meta, 'indexes', ())]
    indexes += custom_indexes

    if is_child:
        indexes.append(parse_index('_cls'))

    # Finally parse our own fields (i.e. not inherited) for unique indexes
    def parse_field(mongo_path, path, field):
        if field.unique:
            index = {'unique': True, 'key': [mongo_path]}
            if not field.required or field.allow_none:
                index['sparse'] = True
            if is_child:
                index['key'].append('_cls')
            indexes.append(parse_index(index))

    for name, field in _collect_fields(nmspc)[1].items():
        parse_field(name or field.attribute, name, field)
        if hasattr(field, 'map_to_field'):
            field.map_to_field(name or field.attribute, name, parse_field)

    return indexes, custom_indexes


class DocumentOpts:

    def __repr__(self):
        return ('<{ClassName}('
                'abstract={self.abstract}, '
                'allow_inheritance={self.allow_inheritance}, '
                'is_child={self.is_child}, '
                'base_schema_cls={self.base_schema_cls}, '
                'indexes={self.indexes}, '
                'custom_indexes={self.custom_indexes}, '
                'collection={self.collection}, '
                'lazy_collection={self.lazy_collection}, '
                'dal={self.dal},'
                'children={self.children})>'
                .format(ClassName=self.__class__.__name__, self=self))

    def __init__(self, name, nmspc, bases):
        meta = nmspc.get('Meta')
        self.abstract = getattr(meta, 'abstract', False)
        self.allow_inheritance = getattr(meta, 'allow_inheritance', self.abstract)
        self.register_document = getattr(meta, 'register_document', True)
        for field in ('collection', 'lazy_collection', 'dal'):
            setattr(self, field, getattr(meta, field, None))
        self.base_schema_cls = getattr(meta, 'base_schema_cls', Schema)
        self.indexes, self.custom_indexes = _collect_indexes(nmspc, bases)
        self.is_child = _is_child(bases)
        self.children = set()
        if self.abstract and not self.allow_inheritance:
            raise DocumentDefinitionError("Abstract document cannot disable inheritance")
        # Handle option inheritance and integrity checks
        for base in bases:
            popts = base.opts
            # Notify the parent of it newborn !
            popts.children.add(name)
            if not popts.allow_inheritance:
                raise DocumentDefinitionError("Document %r doesn't allow inheritance" % base)
            if self.abstract and not popts.abstract:
                raise DocumentDefinitionError(
                    "Abstract document should have all it parents abstract")
            # Retrieve collection related stuff by inheritance
            for field in ('collection', 'lazy_collection', 'dal'):
                candidate = getattr(popts, field)
                curr = getattr(self, field)
                if candidate:
                    if curr:
                        raise DocumentDefinitionError(
                            "%s cannot be defined multiple times (got `%s` and `%s`)" %
                            (field, curr, candidate))
                    else:
                        setattr(self, field, candidate)
        # Handle collection & dal configuration
        if self.abstract:
            not_allowed = [f for f in ('collection', 'lazy_collection', 'dal')
                           if getattr(self, f)]
            if not_allowed:
                raise DocumentDefinitionError("Fields %s are not allowed in abstract document")
        elif self.collection:
            if self.lazy_collection:
                raise NoCollectionDefinedError("Cannot define at the same"
                    " time `collection` and `lazy_collection`")
            if not self.dal:
                # Try to determine dal from the collection itself
                from .dal import find_dal_from_collection
                self.dal = find_dal_from_collection(self.collection)
            if not self.dal:
                raise NoCollectionDefinedError(
                    "No DAL available for collection %s" % self.collection)
        elif self.lazy_collection:
            if not self.dal:
                raise NoCollectionDefinedError(
                    "`dal` attribute is required when using `lazy_collection`")
            if not issubclass(self.dal, AbstractDal):
                raise NoCollectionDefinedError(
                    "`dal` attribute must be a subclass of %s" % AbstractDal)


def _base_meta_document(name, bases, nmspc, base_schema_cls=Schema):
    # Retrieve inherited schema classes
    schema_bases = tuple([getattr(base, 'Schema') for base in bases if hasattr(base, 'Schema')])
    if not schema_bases:
        schema_bases = (base_schema_cls,)
    doc_nmspc, schema_nmspc = _collect_fields(nmspc)
    # Need to create a custom Schema class to use the provided fields
    schema_cls = type('%sSchema' % name, schema_bases, schema_nmspc)
    doc_nmspc['Schema'] = schema_cls
    doc_nmspc['schema'] = schema_cls()
    return name, bases, doc_nmspc


class MetaEmbeddedDocument(type):

    def __new__(cls, name, bases, nmspc):
        name, bases, nmspc = _base_meta_document(
            name, bases, nmspc, base_schema_cls=EmbeddedSchema)
        gen_cls = type.__new__(cls, name, bases, nmspc)
        return gen_cls


class MetaDocument(type):

    BASE_DOCUMENT_CLS = None

    def __new__(cls, name, bases, nmspc):
        # Root Document class has a special handling
        if not cls.BASE_DOCUMENT_CLS:
            cls.BASE_DOCUMENT_CLS = type.__new__(cls, name, bases, nmspc)
            return cls.BASE_DOCUMENT_CLS
        # Generic handling (i.e. for all other documents)
        assert '_cls' not in nmspc, '`_cls` is a reserved attribute'
        # Generate options from the Meta class and inheritance
        opts = DocumentOpts(name, nmspc, bases)
        # If Document is a child, _cls field must be added to the schema
        if opts.is_child:
            from .fields import StrField
            nmspc['_cls'] = StrField(dump_only=True, missing=name)
        # Extract fields and generate the schema
        name, bases, nmspc = _base_meta_document(
            name, bases, nmspc, base_schema_cls=opts.base_schema_cls)
        # Don't alter nmspc before defining schema to avoid shadowing fields
        nmspc['opts'] = opts
        nmspc['_collection'] = None
        # Non-abstract document inherit a dal to implement driver-related stuff
        if opts.dal:
            bases = bases + (opts.dal, )
            # Patch the schema to add the io_validate stuff
            opts.dal.io_validate_patch_schema(nmspc['schema'])
        # Finally create the Document class and register it
        gen_cls = type.__new__(cls, name, bases, nmspc)
        if opts.register_document:
            register_document(gen_cls)
        return gen_cls

    @property
    def collection(self):
        # This is defined inside the metaclass to give property
        # access to the generated class
        if not self._collection:
            self._collection = self.opts.collection
            if not self._collection:
                lazy_collection = self.opts.lazy_collection
                if not lazy_collection:
                    raise NoCollectionDefinedError("No collection nor lazy_collection defined")
                self._collection = lazy_collection()
                if not self._collection:
                    raise NoCollectionDefinedError("lazy_collection didn't returned a collection")
        return self._collection
