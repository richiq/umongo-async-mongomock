from marshmallow import validates_schema, ValidationError
from marshmallow import Schema as MaSchema


__all__ = ('BaseSchema', 'Schema', 'EmbeddedSchema', 'on_need_add_id_field')


class BaseSchema(MaSchema):
    """
    All schema used in umongo should inherit from this base schema
    """

    @validates_schema(pass_original=True)
    def check_unknown_fields(self, data, original_data):
        loadable_fields = [k for k, v in self.fields.items() if not v.dump_only]
        for key in original_data:
            if key not in loadable_fields:
                raise ValidationError('Unknown field name {}'.format(key))

    def map_to_field(self, func):
        """
        Apply a function to every field in the schema

        >>> def func(mongo_path, path, field):
        ...     pass
        """
        for name, field in self.fields.items():
            mongo_path = field.attribute or name
            func(mongo_path, name, field)
            if hasattr(field, 'map_to_field'):
                field.map_to_field(mongo_path, name, func)


def on_need_add_id_field(fields):
    """
    If the given fields make no reference to `_id`, add an `id` field
    (type ObjectId, dump_only=True, attribute=`_id`) to handle it
    """
    for name, field in fields.items():
        if (name == '_id' and not field.attribute) or field.attribute == '_id':
            return
    from .fields import ObjectIdField
    fields['id'] = ObjectIdField(attribute='_id', dump_only=True)


class Schema(BaseSchema):
    """
    Base schema class used by :class:`umongo.Document`
    """

    pass


class EmbeddedSchema(BaseSchema):
    """
    Base schema class used by :class:`umongo.EmbeddedDocument`
    """

    pass
