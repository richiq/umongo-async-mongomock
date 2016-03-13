from datetime import datetime
from marshmallow import ValidationError, missing
from marshmallow import fields as ma_fields

from .registerer import retrieve_document
from .data_objects import BaseDataObject, Reference, List, Dict
from .abstract import BaseField


__all__ = (
    'FieldField',
    'RawField',
    'NestedField',
    'DictField',
    'ListField',
    'StringField',
    'UUIDField',
    'NumberField',
    'IntegerField',
    'DecimalField',
    'BooleanField',
    'FormattedStringField',
    'FloatField',
    'DateTimeField',
    'TimeField',
    'DateField',
    'TimeDeltaField',
    'UrlField',
    'URLField',
    'EmailField',
    'MethodField',
    'FunctionField',
    'StrField',
    'BoolField',
    'IntField',
    'ConstantField',
    'ObjectIdField',
    'ReferenceField',
    'EmbeddedField'
)


# Republish supported mashmallow fields


class RawField(BaseField, ma_fields.Raw):
    pass


class NestedField(BaseField, ma_fields.Nested):
    pass


class DictField(BaseField, ma_fields.Dict):

    def _deserialize(self, value, attr, data):
        value = super()._deserialize(value, attr, data)
        return self._deserialize_from_mongo(value)

    def _deserialize_from_mongo(self, value):
        if value:
            return Dict(value)
        else:
            return Dict()


class ListField(BaseField, ma_fields.List):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('default', [])
        kwargs.setdefault('missing', List)
        super().__init__(*args, **kwargs)

    def _deserialize(self, value, attr, data):
        value = super()._deserialize(value, attr, data)
        return self._deserialize_from_mongo(value)

    def _serialize_to_mongo(self, obj):
        if not obj:
            return missing
        return [self.container.serialize_to_mongo(each) for each in obj]

    def _deserialize_from_mongo(self, value):
        if value:
            return List([self.container.deserialize_from_mongo(each) for each in value])
        else:
            return List()


class StringField(BaseField, ma_fields.String):
    pass


class UUIDField(BaseField, ma_fields.UUID):
    pass


class NumberField(BaseField, ma_fields.Number):
    pass


class IntegerField(BaseField, ma_fields.Integer):
    pass


class DecimalField(BaseField, ma_fields.Decimal):
    pass


class BooleanField(BaseField, ma_fields.Boolean):
    pass


class FormattedStringField(BaseField, ma_fields.FormattedString):
    pass


class FloatField(BaseField, ma_fields.Float):
    pass


class DateTimeField(BaseField, ma_fields.DateTime):
    def _deserialize(self, value, attr, data):
        if isinstance(value, datetime):
            return value
        return super()._deserialize(value, attr, data)


class LocalDateTimeField(BaseField, ma_fields.LocalDateTime):
    pass


class TimeField(BaseField, ma_fields.Time):
    pass


class DateField(BaseField, ma_fields.Date):
    pass


class TimeDeltaField(BaseField, ma_fields.TimeDelta):
    pass


class UrlField(BaseField, ma_fields.Url):
    pass


class URLField(BaseField, ma_fields.URL):
    pass


class EmailField(BaseField, ma_fields.Email):
    pass


class MethodField(BaseField, ma_fields.Method):
    pass


class FunctionField(BaseField, ma_fields.Function):
    pass


class StrField(BaseField, ma_fields.Str):
    pass


class BoolField(BaseField, ma_fields.Bool):
    pass


class IntField(BaseField, ma_fields.Int):
    pass


class ConstantField(BaseField, ma_fields.Constant):
    pass


# Bonus: new fields !


# ObjectIdField is declared in schema to prevent recursive import error
from .schema import ObjectIdField  # noqa


class ReferenceField(ObjectIdField):

    def __init__(self, document_cls, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._document_cls = document_cls

    @property
    def document_cls(self):
        if isinstance(self._document_cls, str):
            self._document_cls = retrieve_document(self._document_cls)
        return self._document_cls

    def _serialize(self, value, attr, obj):
        return super()._serialize(value.pk, attr, obj)

    def _deserialize(self, value, attr, data):
        if value is None:
            return None
        from .document import Document
        if isinstance(value, Reference):
            if value.document_cls != self.document_cls:
                raise ValidationError("%s reference expected" % self.document_cls.__name__)
            return value
        elif isinstance(value, self.document_cls):
            if not value.created:
                raise ValidationError("Cannot reference a document that has not been created yet")
            value = value.pk
        elif isinstance(value, Document):
            raise ValidationError("%s reference expected" % self.document_cls.__name__)
        value = super()._deserialize(value, attr, data)
        return self._deserialize_from_mongo(value)

    def _serialize_to_mongo(self, obj):
        return obj.pk

    def _deserialize_from_mongo(self, value):
        return Reference(self.document_cls, value)

    def io_validate(self):
        pass  # TODO


class EmbeddedField(BaseField, ma_fields.Nested):

    def __init__(self, embedded_document_cls, *args, **kwargs):
        super().__init__(embedded_document_cls.Schema, *args, **kwargs)
        self._embedded_document_cls = embedded_document_cls

    def _serialize(self, value, attr, obj):
        return value.dump()

    def _deserialize(self, value, attr, data):
        if isinstance(value, self._embedded_document_cls):
            return value
        value = super()._deserialize(value, attr, data)
        return self._deserialize_from_mongo(value)

    def _serialize_to_mongo(self, obj):
        return obj.to_mongo()

    def _deserialize_from_mongo(self, value):
        return self._embedded_document_cls.build_from_mongo(value)
