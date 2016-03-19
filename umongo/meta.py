from marshmallow.fields import Field

from .registerer import register_document
from .exceptions import NoCollectionDefinedError
from .schema import Schema, EmbeddedSchema
from .abstract import AbstractDal


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
    # Create Schema instance if not provided
    if 'schema' not in doc_nmspc:
        doc_nmspc['schema'] = schema_cls()
    return name, bases, doc_nmspc


class MetaEmbeddedDocument(type):

    def __new__(cls, name, bases, nmspc):
        name, bases, nmspc = base_meta_document(
            name, bases, nmspc, default_schema=EmbeddedSchema)
        gen_cls = type.__new__(cls, name, bases, nmspc)
        return gen_cls


class MetaDocument(type):

    def __new__(cls, name, bases, nmspc):
        name, bases, nmspc = base_meta_document(name, bases, nmspc)
        nmspc['_collection'] = None
        # Create config with inheritance
        if 'config' not in nmspc:
            config = {}
            for base in bases:
                config.update(getattr(base, 'config', {}))
            config_cls = nmspc.get('Config')
            if config_cls:
                config.update({k: v for k, v in config_cls.__dict__.items()
                               if not k.startswith('_')})
            nmspc['config'] = config
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
                    raise NoCollectionDefinedError("Not collection nor lazy_collection defined")
                self._collection = lazy_collection()
                if not self._collection:
                    raise NoCollectionDefinedError("lazy_collection didn't returned a collection")
        return self._collection
