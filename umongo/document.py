from marshmallow import Schema, fields, validate

from .exceptions import ValidationError, SchemaFieldNamingClashError, NoDBDefinedError, UpdateError
from .registerer import register_document
from .cursor import UMongoCursor


class MetaDocument(type):
    def __new__(cls, name, bases, nmspc):
        schema_cls = nmspc.get('Schema')
        schema = schema_cls()
        nmspc['_schema'] = schema
        schema_fields = schema.fields.keys()
        naming_clashs = [n for n in nmspc.keys() if n in schema_fields]
        if naming_clashs:
            raise SchemaFieldNamingClashError(
                "Schema's fields %s clash with Document's attributes" % naming_clashs)
        gen_cls = type.__new__(cls, name, bases, nmspc)
        register_document(gen_cls)
        return gen_cls


class Document(metaclass=MetaDocument):

    class Schema(Schema):
        pass

    class Config:
        collection = None
        lazy_collection = None

    def __init__(self, created=False, **kwargs):
        self.data, err = self._schema.load(kwargs)
        if err:
            raise ValidationError(err)
        self.created = created
        self._modified_fields = {}

    def copy(self):
        return self.__class__(created=self.created, **self.data)

    def get_update_payload(self):
        return {'$set': {field: self.data[field] for field in self._modified_fields}}

    @property
    def collection(self):
        return self.get_collection()

    def dump(self):
        data, err = self._schema.dump(self.data)
        if err:
            raise ValidationError(err)
        return data

    def save(self):
        if self.created:
            ret = self.get_collection().update_one(self.id, self.get_update_payload())
            if ret.modified_count != 1:
                raise UpdateError(ret.raw_result)
            self._modified_fields.clear()
        else:
            ret = self.get_collection().insert_one(self.data)
            self.created = True
        return ret

    def __getattr__(self, name):
        data = self.__dict__.get('data')
        if data and name in self._schema.fields:
            return data.get(name)
        else:
            # Default behaviour
            raise AttributeError(name)

    def __setattr__(self, name, value):
        data = self.__dict__.get('data')
        if data and name in self._schema.fields:
            self._modified_fields.add(name)
            # TODO: load here !
            data[name] = value
        else:
            super().__setattr__(name, value)

    @classmethod
    def get_collection(cls):
        collection = getattr(cls.Config, 'collection', None)
        if not collection:
            lazy_collection = getattr(cls.Config, 'lazy_collection', None)
            if not lazy_collection:
                raise NoCollectionDefinedError()
            cls.Config.collection = lazy_collection()
        return collection

    @classmethod
    def find_one(cls, *args, **kwargs):
        ret = cls.get_collection().find_one(*args, **kwargs)
        if ret is not None:
            ret = cls(**ret)
        return ret

    @classmethod
    def find_many(cls, *args, **kwargs):
        cursor = cls.get_collection().find_many(*args, **kwargs)
        return UMongoCursor(cursor)
