from marshmallow.fields import Field

from .registerer import register_document
from .exceptions import NoCollectionDefinedError
from .schema import Schema
from .drivers import find_driver_from_collection


def base_meta_document(name, bases, nmspc):
    # Retrieve Schema
    schema_cls = nmspc.get('Schema')
    if not schema_cls:
        schema_cls = next((getattr(base, 'Schema') for base in bases
                           if hasattr(base, 'Schema')), Schema)
    # Retrieve fields declared inside the class
    schema_nmspc = {}
    for key, item in nmspc.items():
        if isinstance(item, Field):
            schema_nmspc[key] = item
            nmspc.pop(key)
    # Need to create a custom Schema class to use the provided fields
    if schema_nmspc:
        schema_cls = type('SubSchema', (schema_cls, ), schema_nmspc)
        nmspc['Schema'] = schema_cls
    # Create Schema instance if not provided
    if 'schema' not in nmspc:
        nmspc['schema'] = schema_cls()
    return name, bases, nmspc


class MetaEmbeddedDocument(type):

    def __new__(cls, name, bases, nmspc):
        name, bases, nmspc = base_meta_document(name, bases, nmspc)
        gen_cls = type.__new__(cls, name, bases, nmspc)
        return gen_cls


class MetaDocument(type):

    def __new__(cls, name, bases, nmspc):
        name, bases, nmspc = base_meta_document(name, bases, nmspc)
        nmspc['_collection'] = None
        nmspc['_driver'] = None
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
        # Finally create the Document class and register it
        gen_cls = type.__new__(cls, name, bases, nmspc)
        if gen_cls.config.get('register_document'):
            register_document(gen_cls)
        return gen_cls

    @property
    def driver(self):
        if not self._driver:
            self._driver = find_driver_from_collection(self.collection)(self.collection)
        return self._driver

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
