from marshmallow.fields import Field

from .registerer import register_document
from .exceptions import NoCollectionDefinedError, DocumentDefinitionError
from .schema import Schema, EmbeddedSchema
from .abstract import AbstractDal
from .indexes import parse_index


def base_meta_document(name, bases, nmspc, default_schema=Schema):
    # Retrieve Schema
    schema_cls = nmspc.get('Schema')
    if not schema_cls:
        schema_cls = next((getattr(base, 'Schema') for base in bases
                           if hasattr(base, 'Schema')), default_schema)
    # Retrieve fields declared inside the class
    schema_nmspc = {}
    doc_nmspc = {}
    for key, item in nmspc.items():
        if isinstance(item, Field):
            schema_nmspc[key] = item
        else:
            doc_nmspc[key] = item
    # Need to create a custom Schema class to use the provided fields
    if schema_nmspc:
        schema_cls = type('SubSchema', (schema_cls, ), schema_nmspc)
    doc_nmspc['Schema'] = schema_cls
    doc_nmspc['schema'] = schema_cls()
    return name, bases, doc_nmspc


class MetaEmbeddedDocument(type):

    def __new__(cls, name, bases, nmspc):
        name, bases, nmspc = base_meta_document(
            name, bases, nmspc, default_schema=EmbeddedSchema)
        gen_cls = type.__new__(cls, name, bases, nmspc)
        return gen_cls


class MetaDocument(type):

    BASE_DOCUMENT_CLS = None

    def __new__(cls, name, bases, nmspc):
        assert 'schema' not in nmspc
        assert 'config' not in nmspc
        nmspc['_collection'] = None
        # Create config with inheritance
        config = {}
        indexes = []
        is_child = False
        config_cls = nmspc.get('Config')
        abstract = getattr(config_cls, 'abstract', False)
        dal = getattr(config_cls, 'dal', None)
        collection = getattr(config_cls, 'collection', None)
        lazy_collection = getattr(config_cls, 'lazy_collection', None)
        register_document_ = getattr(config_cls, 'register_document', True)
        allow_inheritance = getattr(config_cls, 'allow_inheritance', abstract)
        if abstract and not allow_inheritance:
            raise DocumentDefinitionError("Abstract document cannot disable inheritance")
        for base in bases:
            if not issubclass(base, cls.BASE_DOCUMENT_CLS):
                continue
            base_config = getattr(base, 'config', {})
            if not base_config.get('abstract', False):
                if abstract:
                    raise DocumentDefinitionError(
                        "Abstract document should have all it parents abstract")
                is_child = True
            if not base_config.get('allow_inheritance'):
                raise DocumentDefinitionError(
                    "Document %r doesn't allow inheritance" % base)
            if base_config.get('indexes'):
                indexes.extend(base_config['indexes'])
            if base_config.get('collection'):
                if collection:
                    raise DocumentDefinitionError(
                        "Collection cannot be defined multiple times (got `%s` and `%s`)" %
                        (collection, base_config['collection']))
                else:
                    collection = base_config['collection']
            if base_config.get('lazy_collection'):
                if lazy_collection:
                    raise DocumentDefinitionError(
                        "Lazzy collection cannot be defined multiple"
                        " times (got `%s` and `%s`)" %
                        (lazy_collection, base_config['lazy_collection']))
                else:
                    lazy_collection = base_config['lazy_collection']
            if base_config.get('dal'):
                if dal:
                    raise DocumentDefinitionError(
                        "Lazzy collection cannot be defined multiple"
                        " times (got `%s` and `%s`)" %
                        (dal, base_config['dal']))
                else:
                    dal = base_config['dal']
        if config_cls:
            config.update({k: v for k, v in config_cls.__dict__.items()
                           if not k.startswith('_')})
            if getattr(config_cls, 'indexes', None):
                if is_child:
                    for index in getattr(config_cls, 'indexes'):
                        indexes.append(parse_index(index, base_compound_field='_cls'))
                else:
                    indexes.extend(getattr(config_cls, 'indexes'))
            abstract = getattr(config_cls, 'abstract', False)
        if is_child:
            indexes.append('_cls')
        if collection and lazy_collection:
            raise DocumentDefinitionError(
                "Both `collection` and `lazy_collection` are defined")
        config.update({
            'indexes': [parse_index(index) for index in indexes],
            'abstract': abstract,
            'allow_inheritance': allow_inheritance,
            'lazy_collection': lazy_collection,
            'collection': collection,
            'dal': dal,
            'is_child': is_child,
            'register_document': register_document_
        })
        if abstract and config.get('collection'):
            raise DocumentDefinitionError(
                'Cannot defined a collection for an abstract document')
        nmspc['config'] = config
        # If Document is a child, _cls field must be added to the schema
        if is_child:
            from .fields import StrField
            nmspc['_cls'] = StrField(dump_only=True, missing=name)
        # Now that config is done, we can create the schema
        name, bases, nmspc = base_meta_document(name, bases, nmspc)
        # Find back fields needing unique indexes
        for key, field in nmspc['schema'].fields.items():
            if field.unique:
                index = {'unique': True, 'key': [key or field.attribute]}
                if not field.required or field.allow_none:
                    index['sparse'] = True
                if is_child:
                    index['key'].append('_cls')
                nmspc['config']['indexes'].append(parse_index(index))
        # If a collection has been defined, the document is not abstract.
        # Retrieve it corresponding DAL and make the document inherit it.
        collection = nmspc['config'].get('collection')
        lazy_collection = nmspc['config'].get('lazy_collection')
        dal = nmspc['config'].get('dal')
        if not dal:
            if collection:
                # Try to determine dal from the collection itself
                from .dal import find_dal_from_collection
                dal = find_dal_from_collection(collection)
                if not dal:
                    raise NoCollectionDefinedError(
                        "No DAL available for collection %s" % collection)
            elif lazy_collection:
                raise NoCollectionDefinedError(
                    "`dal` attribute is required when using `lazy_collection`")
        if dal:
            if not issubclass(dal, AbstractDal):
                raise NoCollectionDefinedError(
                    "`dal` attribute must be a subclass of %s" % AbstractDal)
            # Patch the schema to add the io_validate stuff
            dal.io_validate_patch_schema(nmspc['schema'])
            bases = bases + (dal, )
        # Finally create the Document class and register it
        gen_cls = type.__new__(cls, name, bases, nmspc)
        if gen_cls.config.get('register_document'):
            register_document(gen_cls)
        if not cls.BASE_DOCUMENT_CLS:
            cls.BASE_DOCUMENT_CLS = gen_cls
        return gen_cls

    @property
    def collection(self):
        # This is defined inside the metaclass to give property
        # access to the generated class
        if not self._collection:
            self._collection = self.config.get('collection')
            if not self._collection:
                lazy_collection = self.config.get('lazy_collection')
                if not lazy_collection:
                    raise NoCollectionDefinedError("No collection nor lazy_collection defined")
                self._collection = lazy_collection()
                if not self._collection:
                    raise NoCollectionDefinedError("lazy_collection didn't returned a collection")
        return self._collection
