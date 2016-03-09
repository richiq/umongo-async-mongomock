from marshmallow.fields import Field

from .data_proxy import DataProxy
from .abstract import BaseWrappedData
from .registerer import register_document
from .exceptions import NoCollectionDefinedError, UpdateError
from .schema import Schema


class MetaDocument(type):

    def __new__(cls, name, bases, nmspc):
        nmspc['_collection'] = None
        # Retrieve Schema
        schema_cls = nmspc.get('Schema')
        if not schema_cls:
            schema_cls = next(getattr(base, 'Schema') for base in bases
                              if hasattr(base, 'Schema'))
        # Retrieve fields declared inside the class
        schema_nmspc = {}
        for key, item in nmspc.items():
            if isinstance(item, Field):
                schema_nmspc[k] = v
                nmspc.pop(k)
        # Need to create a custom Schema class to use the provided fields
        if schema_nmspc:
            schema_cls = type('SubSchema', (schema_cls, ), schema_nmspc)
            nmspc['Schema'] = schema_cls
        # Create Schema instance if not provided
        if 'schema' not in nmspc:
            nmspc['schema'] = schema_cls()
        # Create config with inheritance
        if 'config' not in nmspc:
            config = {}
            for base in bases:
                config.update(getattr(base, 'config', {}))
            config_cls = nmspc.get('Config')
            if config_cls:
                config.update({k: v for k, v in config_cls.__dict__.items() if not k.startswith('_')})
            nmspc['config'] = config
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


class Document(BaseWrappedData, metaclass=MetaDocument):

    Schema = Schema

    class Config:
        collection = None
        lazy_collection = None
        register_document = True

    def __init__(self, **kwargs):
        self.created = False
        self.data = DataProxy(self.schema, kwargs)

    @property
    def pk(self):
        return self.data._data.get('_id')

    @property
    def name(self):
        return self.__name__

    @classmethod
    def build_from_mongo(cls, data, partial=False):
        doc = cls()
        doc.from_mongo(data, partial=partial)
        return doc

    def from_mongo(self, data, partial=False):
        # TODO: handle partial
        self.data.from_mongo(data, partial=partial)
        self.created = True

    def to_mongo(self, update=False):
        return self.data.to_mongo(update=update)

    def dump(self):
        return self.data.dump()

    def reload(self):
        if not self.created:
            raise NotCreatedError('Cannot reload a document that'
                                  ' has not been committed yet')
        ret = self.collection.find_one(self.pk)
        if ret is None:
            raise NotCreatedError("Document doesn't exists in database")
        self.data = DataProxy(self.schema)
        self.data.from_mongo(ret)

    def commit(self, io_validate_all=False):
        # TODO: implement in driver
        self.data.io_validate(validate_all=io_validate_all)
        payload = self.data.to_mongo(update=self.created)
        if self.created:
            if payload:
                ret = self.collection.update_one(
                    {'_id': self.data.get_by_mongo_name('_id')}, payload)
                if ret.modified_count != 1:
                    raise UpdateError(ret.raw_result)
        else:
            ret = self.collection.insert_one(payload)
            # TODO: check ret ?
            self.data.set_by_mongo_name('_id', ret.inserted_id)
            self.created = True
        self.data.clear_modified()
        return self

    @property
    def collection(self):
        # Cannot implicitly access to the class's property
        return type(self).collection

    @classmethod
    def find_one(cls, *args, **kwargs):
        ret = cls.collection.find_one(*args, **kwargs)
        if ret is not None:
            ret = cls.build_from_mongo(ret)
        return ret

    @classmethod
    def find(cls, *args, **kwargs):
        from .cursor import Cursor
        cursor = cls.collection.find(*args, **kwargs)
        return Cursor(cls, cursor)
