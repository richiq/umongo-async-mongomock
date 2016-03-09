from datetime import datetime
from marshmallow import ValidationError, missing
from marshmallow import fields as ma_fields

from .registerer import retrieve_document
from .wrapped_data import Reference, List


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


class FieldField(ma_fields.Field):
    pass


class RawField(ma_fields.Raw):
    pass


class NestedField(ma_fields.Nested):
    pass


class DictField(ma_fields.Dict):
    pass


class ListField(ma_fields.List):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('default', [])
        kwargs.setdefault('missing', list)
        super().__init__(*args, **kwargs)

    def _deserialize(self, value, attr, data):
        value = super()._deserialize(value, attr, data)
        return self._deserialize_from_mongo(value)

    def _serialize_to_mongo(self, value):
        if not value:
            return missing
        if hasattr(self.container, '_serialize_to_mongo'):
            return [self.container._serialize_to_mongo(each) for each in value]
        else:
            return list(value)

    def _deserialize_from_mongo(self, value):
        return List(value) if value else List()


class StringField(ma_fields.String):
    pass


class UUIDField(ma_fields.UUID):
    pass


class NumberField(ma_fields.Number):
    pass


class IntegerField(ma_fields.Integer):
    pass


class DecimalField(ma_fields.Decimal):
    pass


class BooleanField(ma_fields.Boolean):
    pass


class FormattedStringField(ma_fields.FormattedString):
    pass


class FloatField(ma_fields.Float):
    pass


class DateTimeField(ma_fields.DateTime):
    def _deserialize(self, value, attr, data):
        if isinstance(value, datetime):
            return value
        return super()._deserialize(value, attr, data)


class LocalDateTimeField(ma_fields.LocalDateTime):
    pass


class TimeField(ma_fields.Time):
    pass


class DateField(ma_fields.Date):
    pass


class TimeDeltaField(ma_fields.TimeDelta):
    pass


class UrlField(ma_fields.Url):
    pass


class URLField(ma_fields.URL):
    pass


class EmailField(ma_fields.Email):
    pass


class MethodField(ma_fields.Method):
    pass


class FunctionField(ma_fields.Function):
    pass


class StrField(ma_fields.Str):
    pass


class BoolField(ma_fields.Bool):
    pass


class IntField(ma_fields.Int):
    pass


class ConstantField(ma_fields.Constant):
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

    def _serialize_to_mongo(self, value):
        return value.pk

    def _deserialize_from_mongo(self, value):
        return Reference(self.document_cls, value)

    def io_validate(self):
        pass  # TODO


class EmbeddedField(ma_fields.Dict):

    def __init__(self, embedded_document_cls, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._embedded_document_cls = embedded_document_cls

    def _serialize(self, value, attr, obj):
        return value.dump()

    def _deserialize(self, value, attr, data):
        if isinstance(value, self._embedded_document_cls):
            return value
        value = super()._deserialize(value, attr, data)
        return self._deserialize_from_mongo(value)

    def _serialize_to_mongo(self, value):
        return value.to_mongo()

    def _deserialize_from_mongo(self, value):
        embedded_document = self._embedded_document_cls()
        embedded_document.load(value)
        return embedded_document
