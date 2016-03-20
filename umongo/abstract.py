from marshmallow import fields as ma_fields, missing


class BaseField(ma_fields.Field):

    def __init__(self, *args, io_validate=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.io_validate = io_validate

    def __repr__(self):
        return ('<fields.{ClassName}(default={self.default!r}, '
                'attribute={self.attribute!r}, '
                'validate={self.validate}, required={self.required}, '
                'load_only={self.load_only}, dump_only={self.dump_only}, '
                'missing={self.missing}, allow_none={self.allow_none}, '
                'error_messages={self.error_messages}, '
                'io_validate={self.io_validate})>'
                .format(ClassName=self.__class__.__name__, self=self))

    def serialize(self, attr, obj, accessor=None):
        return super().serialize(attr, obj, accessor=accessor)

    def deserialize(self, value, attr=None, data=None):
        return super().deserialize(value, attr=attr, data=data)

    def serialize_to_mongo(self, obj):
        if obj is missing:
            return missing
        return self._serialize_to_mongo(obj)

    # def serialize_to_mongo_update(self, path, obj):
    #     return self._serialize_to_mongo(attr, obj=obj, update=update)

    def deserialize_from_mongo(self, value):
        return self._deserialize_from_mongo(value)

    def _serialize_to_mongo(self, obj):
        return obj

    # def _serialize_to_mongo_update(self, ):
    #     if isinstance(obj, BaseDataObject):
    #         return obj.to_mongo(attr=attr, update=update)
    #     elif update:
    #         return {attr: obj}
    #     else:
    #         return obj

    def _deserialize_from_mongo(self, value):
        return value


class BaseDataObject:

    def __init__(self, *args, **kwargs):
        self._modified = False
        super().__init__(*args, **kwargs)

    def is_modified(self):
        return self._modified

    def set_modified(self):
        self._modified = True

    def clear_modified(self):
        self._modified = False

    @classmethod
    def build_from_mongo(cls, data):
        doc = cls()
        doc.from_mongo(data)
        return doc

    def from_mongo(self, data):
        return self(data)

    def to_mongo(self, update=False):
        return self

    def dump(self):
        return self


class AbstractDal:

    @staticmethod
    def is_compatible_with(collection):
        raise NotImplementedError

    def reload(self):
        raise NotImplementedError

    def commit(self, io_validate_all=False):
        raise NotImplementedError

    def delete(self):
        raise NotImplementedError

    @classmethod
    def find_one(cls, *args, **kwargs):
        raise NotImplementedError

    @classmethod
    def find(cls, *args, **kwargs):
        raise NotImplementedError

    def io_validate(self, validate_all=False):
        raise NotImplementedError

    @staticmethod
    def io_validate_patch_schema(schema):
        raise NotImplementedError
