from marshmallow import validates_schema, ValidationError, missing
from marshmallow import Schema as MaSchema

from . import fields


__all__ = ('Schema', 'BaseSchema')


class BaseSchema(MaSchema):

    @validates_schema(pass_original=True)
    def check_unknown_fields(self, data, original_data):
        for key in original_data:
            if key not in self.fields:
                raise ValidationError('Unknown field name {}'.format(key))


class Schema(BaseSchema):

    id = fields.ObjectIdField(attribute='_id')
