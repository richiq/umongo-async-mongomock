import bson
from marshmallow import validates_schema, ValidationError
from marshmallow import Schema as MaSchema
from marshmallow import fields as ma_fields

from .abstract import BaseField


__all__ = ('BaseSchema', 'Schema', 'EmbeddedSchema')


# Declare the ObjectIdField here to prevent recursive import error with fields
class ObjectIdField(BaseField, ma_fields.Field):

    def _serialize(self, value, attr, obj):
        if value is None:
            return None
        return str(value)

    def _deserialize(self, value, attr, data):
        if value is None:
            return None
        try:
            return bson.ObjectId(value)
        except bson.errors.InvalidId:
            raise ValidationError('Invalid ObjectId')


class BaseSchema(MaSchema):

    @validates_schema(pass_original=True)
    def check_unknown_fields(self, data, original_data):
        for key in original_data:
            if key not in self.fields:
                raise ValidationError('Unknown field name {}'.format(key))


class Schema(BaseSchema):

    id = ObjectIdField(attribute='_id')


class EmbeddedSchema(BaseSchema):
    pass
