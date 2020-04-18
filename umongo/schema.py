from marshmallow.fields import Field

from . import fields
from .abstract import BaseSchema


__all__ = ('Schema', 'EmbeddedSchema', 'on_need_add_id_field', 'add_child_field')


def on_need_add_id_field(bases, fields_dict):
    """
    If the given fields make no reference to `_id`, add an `id` field
    (type ObjectId, dump_only=True, attribute=`_id`) to handle it
    """

    def find_id_field(fields_dict):
        for name, field in fields_dict.items():
            # Skip fake fields present in schema (e.g. `post_load` decorated function)
            if not isinstance(field, Field):
                continue
            if (name == '_id' and not field.attribute) or field.attribute == '_id':
                return name, field
        return None

    # Search among parents for the id field
    for base in bases:
        schema = base()
        if find_id_field(schema.fields):
            return

    # Search amongo our own fields
    if not find_id_field(fields_dict):
        # No id field found, add a default one
        fields_dict['id'] = fields.ObjectIdField(attribute='_id', dump_only=True)


def add_child_field(name, fields_dict):
    fields_dict['cls'] = fields.StringField(attribute='_cls', default=name, dump_only=True)


class Schema(BaseSchema):
    """Base schema class used by :class:`umongo.Document`"""


class EmbeddedSchema(BaseSchema):
    """Base schema class used by :class:`umongo.EmbeddedDocument`"""
