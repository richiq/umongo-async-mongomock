import bson
from datetime import datetime
from marshmallow import ValidationError
from marshmallow.fields import *  # noqa, republishing

from .registerer import retrieve_document


class ObjectId(Field):

    def _serialize(self, value, attr, obj):
        if value is None:
            return None
        return str(value)

    def _deserialize(self, value, attr, data):
        if value is None:
            return None
        try:
            return bson.ObjectId(value)
        except ValueError:
            raise ValidationError('Invalid ObjectId')


class UMongoReference:
    def __init__(self, document_cls, oid):
        self._document_cls = document_cls
        self.id = oid
        self._document = None

    def get(self):
        # Sync version
        if not self._document:
            if self.id is None:
                raise ReferenceError('Cannot retrieve a None Reference')
            if isinstance(self._document_cls, str):
                self._document_cls = retrieve_document_cls(self._document_cls)
            self._document = self._document_cls.find_one(self.id)
            if not self._document:
                raise ValidationError(
                    'Reference not found for document %s.' % self._document_cls.__name__)
        return self._document


class Reference(ObjectId):

    def __init__(self, document_cls, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._document_cls = document_cls

    def _serialize(self, value, attr, obj):
        if value.id is None:
            return None
        return str(value.id)

    def _deserialize(self, value, attr, data):
        value = super()._deserialize(value, attr, data)
        return UMongoReference(self._document_cls, value)


class DateTime(DateTime):
    def _deserialize(self, value, attr, data):
        if isinstance(value, datetime):
            return value
        return super()._deserialize(value, attr, data)
