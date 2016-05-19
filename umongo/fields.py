from datetime import datetime
from marshmallow import ValidationError, missing
from marshmallow import fields as ma_fields
from bson import DBRef, ObjectId, errors as bson_errors

# from .registerer import retrieve_document
from .exceptions import NotRegisteredDocumentError
from .data_objects import Reference, List, Dict
from .abstract import BaseField
from .i18n import gettext as _


__all__ = (
    # 'RawField',
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
    # 'TimeField',
    # 'DateField',
    # 'TimeDeltaField',
    'UrlField',
    'URLField',
    'EmailField',
    # 'MethodField',
    # 'FunctionField',
    'StrField',
    'BoolField',
    'IntField',
    'ConstantField',
    'ObjectIdField',
    'ReferenceField',
    'GenericReferenceField',
    'EmbeddedField'
)


# Republish supported mashmallow fields


# class RawField(BaseField, ma_fields.Raw):
#     pass


class DictField(BaseField, ma_fields.Dict):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('default', {})
        kwargs.setdefault('missing', Dict)
        super().__init__(*args, **kwargs)

    def _deserialize(self, value, attr, data):
        value = super()._deserialize(value, attr, data)
        return self._deserialize_from_mongo(value)

    def _serialize_to_mongo(self, obj):
        if not obj:
            return missing
        return dict(obj)

    def _deserialize_from_mongo(self, value):
        if value:
            return Dict(value)
        else:
            return Dict()


class ListField(BaseField, ma_fields.List):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('default', [])
        kwargs.setdefault('missing', lambda: List(self.container))
        super().__init__(*args, **kwargs)

    def _deserialize(self, value, attr, data):
        return List(self.container, super()._deserialize(value, attr, data))
        # return self._deserialize_from_mongo(value)

    def _serialize_to_mongo(self, obj):
        if not obj:
            return missing
        return [self.container.serialize_to_mongo(each) for each in obj]

    def _deserialize_from_mongo(self, value):
        if value:
            return List(self.container, [self.container.deserialize_from_mongo(each)
                                         for each in value])
        else:
            return List(self.container)

    def map_to_field(self, mongo_path, path, func):
        """Apply a function to every field in the schema
        """
        func(mongo_path, path, self.container)
        if hasattr(self.container, 'map_to_field'):
            self.container.map_to_field(mongo_path, path, func)


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

    def _deserialize(self, value, attr, data):
        if isinstance(value, datetime):
            return value
        return super()._deserialize(value, attr, data)


# class TimeField(BaseField, ma_fields.Time):
#     pass


# class DateField(BaseField, ma_fields.Date):
#     pass


# class TimeDeltaField(BaseField, ma_fields.TimeDelta):
#     pass


class UrlField(BaseField, ma_fields.Url):
    pass


class EmailField(BaseField, ma_fields.Email):
    pass


# class MethodField(BaseField, ma_fields.Method):
#     pass


# class FunctionField(BaseField, ma_fields.Function):
#     pass


class ConstantField(BaseField, ma_fields.Constant):
    pass


# Aliases
URLField = UrlField
StrField = StringField
BoolField = BooleanField
IntField = IntegerField


# Bonus: new fields !


class ObjectIdField(BaseField, ma_fields.Field):
    """
    Marshmallow field for :class:`bson.ObjectId`
    """

    def _serialize(self, value, attr, obj):
        if value is None:
            return None
        return str(value)

    def _deserialize(self, value, attr, data):
        if value is None:
            return None
        try:
            return ObjectId(value)
        except bson_errors.InvalidId:
            raise ValidationError(_('Invalid ObjectId.'))


class ReferenceField(ObjectIdField):

    def __init__(self, document_cls, *args, reference_cls=Reference, **kwargs):
        super().__init__(*args, **kwargs)
        self.reference_cls = reference_cls
        self._document_cls = document_cls

    @property
    def document_cls(self):
        if isinstance(self._document_cls, str):
            self._document_cls = self.instance.retrieve_document(self._document_cls)
        return self._document_cls

    def _serialize(self, value, attr, obj):
        return super()._serialize(value.pk, attr, obj)

    def _deserialize(self, value, attr, data):
        if value is None:
            return None
        from .document import Document
        if isinstance(value, DBRef):
            if self._document_cls.collection.name != value.collection:
                raise ValidationError(_("DBRef must be on collection `{collection}`.").format(
                    self._document_cls.collection.name))
            value = value.id
        elif isinstance(value, Reference):
            if value.document_cls != self.document_cls:
                raise ValidationError(_("`{document}` reference expected.").format(
                    document=self.document_cls.__name__))
            if type(value) is not self.reference_cls:
                value = self.reference_cls(value.document_cls, value.pk)
            return value
        elif isinstance(value, self.document_cls):
            if not value.is_created:
                raise ValidationError(
                    _("Cannot reference a document that has not been created yet."))
            value = value.pk
        elif isinstance(value, Document):
            raise ValidationError(_("`{document}` reference expected.").format(
                document=self.document_cls.__name__))
        value = super()._deserialize(value, attr, data)
        return self._deserialize_from_mongo(value)

    def _serialize_to_mongo(self, obj):
        return obj.pk

    def _deserialize_from_mongo(self, value):
        return self.reference_cls(self.document_cls, value)

    def fetch(self):
        """
        Retrieve in database the document referenced.
        """
        raise NotImplementedError


class GenericReferenceField(BaseField):

    def __init__(self, *args, reference_cls=Reference, **kwargs):
        super().__init__(*args, **kwargs)
        self.reference_cls = reference_cls

    def _serialize(self, value, attr, obj):
        return {'id': str(value.pk), 'cls': value.document_cls.__name__}

    def _deserialize(self, value, attr, data):
        if value is None:
            return None
        from .document import Document
        if isinstance(value, Reference):
            if type(value) is not self.reference_cls:
                value = self.reference_cls(value.document_cls, value.pk)
            return value
        elif isinstance(value, Document):
            if not value.is_created:
                raise ValidationError(
                    _("Cannot reference a document that has not been created yet."))
            return self.reference_cls(value.__class__, value.pk)
        elif isinstance(value, dict):
            if value.keys() != {'cls', 'id'}:
                raise ValidationError(_("Generic reference must have `id` and `cls` fields."))
            try:
                _id = ObjectId(super()._deserialize(value['id'], attr, data))
            except ValueError:
                raise ValidationError(_("Invalid `id` field."))
            return self._deserialize_from_mongo({
                '_cls': value['cls'],
                '_id': _id
            })
        else:
            raise ValidationError(_("Invalid value for generic reference field."))

    def _serialize_to_mongo(self, obj):
        return {'_id': obj.pk, '_cls': obj.document_cls.__name__}

    def _deserialize_from_mongo(self, value):
        try:
            document_cls = self.instance.retrieve_document(value['_cls'])
        except NotRegisteredDocumentError:
            raise ValidationError(_('Unknown document `{document}`.').format(
                document=value['_cls']))
        return self.reference_cls(document_cls, value['_id'])


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

    def map_to_field(self, mongo_path, path, func):
        """Apply a function to every field in the schema
        """
        for name, field in self._embedded_document_cls.schema.fields.items():
            cur_path = '%s.%s' % (path, name)
            cur_mongo_path = '%s.%s' % (mongo_path, field.attribute or name)
            func(cur_mongo_path, cur_path, field)
            if hasattr(field, 'map_to_field'):
                field.map_to_field(cur_mongo_path, cur_path, func)
