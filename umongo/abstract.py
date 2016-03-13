from abc import ABCMeta, abstractstaticmethod, abstractmethod
from marshmallow import fields as ma_fields, missing


class BaseField(ma_fields.Field):

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


# class BaseDataObject(metaclass=ABCMeta):

    # @abstractmethod
    # def __init__(self, schema):
    #     pass

    # @abstractmethod
    # def from_mongo(self, data, partial=False):
    #     pass

    # @abstractmethod
    # def to_mongo(self, update=False):
    #     pass

    # @abstractmethod
    # def load(self, **kwargs):
    #     pass

    # @abstractmethod
    # def dump(self):
    #     pass

    # @abstractmethod
    # def io_validate(self):
    #     pass

    # @abstractmethod
    # def clear_modified(self):
    #     pass


# class BaseField(marshmallow.Field):

#     def serialize(self, value, attr, obj):
#         return super()._serialize(value.pk, attr, obj)

#     def deserialize(self, value, attr, data):
#         return self._deserialize_from_mongo(value)

#     def serialize_to_mongo(self, value):
#         return value

#     def deserialize_from_mongo(self, value):
#         return value

#     def io_validate(self):
#         pass  # TODO


class AbstractDal(metaclass=ABCMeta):

    @abstractstaticmethod
    def is_compatible_with(collection):
        pass

    @abstractmethod
    def reload(self, doc):
        pass

    @abstractmethod
    def commit(self, doc, io_validate_all=False):
        pass

    @abstractmethod
    def delete(self, doc):
        pass

    @abstractmethod
    def find_one(self, doc_cls, *args, **kwargs):
        pass

    @abstractmethod
    def find(self, doc_cls, *args, **kwargs):
        pass


class AbstractCursor:
    # TODO...
    pass
