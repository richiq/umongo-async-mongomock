import bson
from marshmallow import ValidationError
from marshmallow.validate import *  # noqa, republishing


class Reference(marshmallow.validate.Validator):

    default_message = 'Reference not found in collection {collection}.'

    def __init__(self, collection, error=None):
        self.collection = collection
        self.error = error or self.default_message

    def _repr_args(self):
        return 'collection={0!r}'.format(self.collection.name)

    def _format_error(self, value):
        return self.error.format(input=value)

    def __call__(self, value):
        message = self._format_error(value)
        if not self.collection.find_one(value, projection={'_id': True}):
            raise ValidationError(message)
        return value
