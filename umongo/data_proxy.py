from marshmallow import ValidationError, missing
from functools import partial

from .abstract import BaseWrappedData, ChangeTracker
from .exceptions import FieldNotLoadedError


class DataProxy(BaseWrappedData):

    def __init__(self, schema, data=None):
        self.__dict__['partial'] = False
        self.__dict__['_schema'] = schema
        self.__dict__['_fields'] = schema.fields
        self.__dict__['_data'] = {}
        self.__dict__['_modified_data'] = set()
        fields_from_mongo_key = {}
        for k, v in self._fields.items():
            if v.attribute:
                k = v.attribute
            fields_from_mongo_key[k] = v
        self.__dict__['_fields_from_mongo_key'] = fields_from_mongo_key
        if data:
            self.load(data)

    def to_mongo(self, update=False):
        if update:
            return self._to_mongo_update()
        mongo_data = {}
        for k, v in self._data.items():
            if v is not missing:
                field = self._fields_from_mongo_key[k]
                if hasattr(field, '_serialize_to_mongo'):
                    v = field._serialize_to_mongo(v)
                if v is not missing:
                    mongo_data[k] = v
        return mongo_data

    def _to_mongo_update(self):
        mongo_data = {}
        if self._modified_data:
            set_data = {}
            unset_data = []
            for k in self._modified_data:
                v = self._data[k]
                field = self._fields_from_mongo_key[k]
                if v is not missing and hasattr(field, '_serialize_to_mongo'):
                    v = field._serialize_to_mongo(v)
                if v is missing:
                    unset_data.append(k)
                else:
                    set_data[k] = v
            if set_data:
                mongo_data['$set'] = set_data
            if unset_data:
                mongo_data['$unset'] = sorted(unset_data)
        return mongo_data or None

    def from_mongo(self, data, partial=False):
        self._data = {}
        for k, v in data.items():
            field = self._fields_from_mongo_key[k]
            if hasattr(field, '_deserialize_from_mongo'):
                v = field._deserialize_from_mongo(v)
            self._data[k] = v
        self.clear_modified()
        self._connect_data_change_trackers()
        self.partial = partial

    def dump(self):
        data, err = self._schema.dump(self._data)
        if err:
            raise ValidationError(err)
        return data

    def _mark_as_modified(self, key):
        self._modified_data.add(key)

    def _connect_data_change_trackers(self):
        for k, v in self._data.items():
            if isinstance(v, ChangeTracker):
                v.change_tracker_connect(partial(self._mark_as_modified, k))

    def load(self, data, partial=False):
        data, err = self._schema.load(data)
        if err:
            raise ValidationError(err)
        self._data = data
        self._connect_data_change_trackers()
        self.clear_modified()
        self.partial = partial

    def get_by_mongo_name(self, name):
        return self._data[name]

    def set_by_mongo_name(self, name, value):
        self._data[name] = value
        self._mark_as_modified(name)

    def del_by_mongo_name(self, name):
        self.set_by_mongo_name(name, missing)

    def __getitem__(self, name):
        if name not in self._fields:
            raise KeyError(name)
        name = self._fields[name].attribute or name
        value = self._data.get(name)
        if value is missing:
            if self.partial:
                raise FieldNotLoadedError(name)
            else:
                return None
        return value

    def __delitem__(self, name):
        if name not in self._fields:
            raise KeyError(name)
        name = self._fields[name].attribute or name
        if self._data[name] is missing:
            raise KeyError(name)
        self._data[name] = missing
        self._mark_as_modified(name)

    def __setitem__(self, name, value):
        if name not in self._fields:
            raise KeyError(name)
        field = self._fields[name]
        name = field.attribute or name
        value = field._deserialize(value, name, None)
        self._data[name] = value
        if isinstance(value, ChangeTracker):
            value.change_tracker_connect(partial(self._mark_as_modified, name))
        self._mark_as_modified(name)

    def __setattr__(self, name, value):
        if name in self.__dict__:
            self.__dict__[name] = value
        else:
            self[name] = value

    def __getattr__(self, name):
        return self[name]

    def __delattr__(self, name):
        del self[name]

    def __repr__(self):
        return "<DataProxy(%s)>" % self._data

    def __eq__(self, other):
        if isinstance(other, dict):
            return self._data == other
        else:
            return self._data == other._data

    def clear_modified(self):
        self._modified_data.clear()

    def io_validate(self, validate_all=False):
        # TODO: handle required here
        # TODO: handle unique here
        pass
