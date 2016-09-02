from marshmallow import ValidationError
from marshmallow import fields as ma_fields
import bson

from .i18n import gettext as _


__all__ = (
    'ObjectId',
    'GenericReference',
)


# Bonus: new fields !


class ObjectId(ma_fields.Field):
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
            return bson.ObjectId(value)
        except bson.errors.InvalidId:
            raise ValidationError(_('Invalid ObjectId.'))


class Reference(ObjectId):
    """
    Mashmallow field for :class:`umongo.fields.ReferenceField`
    """

    def __init__(self, *args, mongo_world=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.mongo_world = mongo_world

    def _serialize(self, value, attr, obj):
        if value is None:
            return None
        if self.mongo_world:
            # In mongo world, value is a regular ObjectId
            return str(value)
        else:
            # In OO world, value is a :class:`umongo.data_object.Reference`
            return str(value.pk)


class GenericReference(ma_fields.Field):
    """
    Mashmallow field for :class:`umongo.fields.GenericReferenceField`
    """

    def __init__(self, *args, mongo_world=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.mongo_world = mongo_world

    def _serialize(self, value, attr, obj):
        if value is None:
            return None
        if self.mongo_world:
            # In mongo world, value a dict of cls and id
            return {'id': str(value['_id']), 'cls': value['_cls']}
        else:
            # In OO world, value is a :class:`umongo.data_object.Reference`
            return {'id': str(value.pk), 'cls': value.document_cls.__name__}

    def _deserialize(self, value, attr, data):
        if value is None:
            return None
        if not isinstance(value, dict):
            raise ValidationError(_("Invalid value for generic reference field."))
        if value.keys() != {'cls', 'id'}:
            raise ValidationError(_("Generic reference must have `id` and `cls` fields."))
        try:
            _id = bson.ObjectId(value['id'])
        except ValueError:
            raise ValidationError(_("Invalid `id` field."))
        if self.mongo_world:
            return {'_cls': value['cls'], '_id': _id}
        else:
            return {'cls': value['cls'], 'id': _id}
