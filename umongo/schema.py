from .abstract import BaseSchema


__all__ = ('Schema', 'EmbeddedSchema', 'on_need_add_id_field')


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
