from txmongo.collection import Collection
from twisted.internet.defer import inlineCallbacks

from ..abstract import AbstractDal
from ..data_proxy import DataProxy, missing
from ..exceptions import NotCreatedError, UpdateError, DeleteError, ValidationError
from ..fields import ReferenceField, ListField, EmbeddedField


class TxMongoDal(AbstractDal):

    @staticmethod
    def is_compatible_with(collection):
        return isinstance(collection, Collection)

    @staticmethod
    def io_validate_patch_schema(schema):
        _io_validate_patch_schema(schema)

    @inlineCallbacks
    def reload(self):
        ret = yield self.collection.find_one(self.pk)
        if ret is None:
            raise NotCreatedError("Document doesn't exists in database")
        self._data = DataProxy(self.schema)
        self._data.from_mongo(ret)

    @inlineCallbacks
    def commit(self, io_validate_all=False):
        self.io_validate(validate_all=io_validate_all)
        payload = self._data.to_mongo(update=self.created)
        if self.created:
            if payload:
                ret = yield self.collection.update_one(
                    {'_id': self._data.get_by_mongo_name('_id')}, payload)
                if ret.modified_count != 1:
                    raise UpdateError(ret.raw_result)
        else:
            ret = yield self.collection.insert_one(payload)
            # TODO: check ret ?
            self._data.set_by_mongo_name('_id', ret.inserted_id)
            self.created = True
        self._data.clear_modified()

    @inlineCallbacks
    def delete(self):
        ret = yield self.collection.delete_one({'_id': self.pk})
        if ret.deleted_count != 1:
            raise DeleteError(ret.raw_result)

    @inlineCallbacks
    def io_validate(self, validate_all=False):
        if validate_all:
            return _io_validate_data_proxy(self.schema, self._data)
        else:
            return _io_validate_data_proxy(
                self.schema, self._data, partial=self._data.get_modified_fields())

    @classmethod
    @inlineCallbacks
    def find_one(cls, *args, **kwargs):
        ret = yield cls.collection.find_one(*args, **kwargs)
        if ret is not None:
            ret = cls.build_from_mongo(ret)
        return ret

    @classmethod
    @inlineCallbacks
    def find(cls, *args, **kwargs):
        raw_cursor_or_list = yield cls.collection.find(*args, **kwargs)
        if isinstance(raw_cursor_or_list, tuple):

            def wrap_raw_results(result):
                cursor = result[1]
                if cursor is not None:
                    cursor.addCallback(wrap_raw_results)
                return ([cls.build_from_mongo(e) for e in result[0]], cursor)

            return wrap_raw_results(raw_cursor_or_list)
        else:
            return [cls.build_from_mongo(e) for e in raw_cursor_or_list]


# Run multiple validators and collect all errors in one
@inlineCallbacks
def _run_validators(validators, field, value):
    if not hasattr(validators, '__iter__'):
        return validators(field, value)
    else:
        errors = []
        for validator in validators:
            try:
                yield validator(field, value)
            except ValidationError as ve:
                errors.extend(ve.messages)
        if errors:
            raise ValidationError(errors)


@inlineCallbacks
def _io_validate_data_proxy(schema, data_proxy, partial=None):
    errors = {}
    for name, field in schema.fields.items():
        if partial and name not in partial:
            continue
        data_name = field.attribute or name
        value = data_proxy._data[data_name]
        try:
            # Also look for required
            field._validate_missing(value)
            if value is not missing:
                if field.io_validate:
                    yield _run_validators(field.io_validate, field, value)
        except ValidationError as ve:
            errors[name] = ve.messages
    if errors:
        raise ValidationError(errors)


@inlineCallbacks
def _reference_io_validate(field, value):
    return
    # raise NotImplementedError


@inlineCallbacks
def _list_io_validate(field, value):
    errors = {}
    validators = field.container.validators
    if not validators:
        return
    for i, e in enumerate(value):
        try:
            yield _run_validators(validators, e)
        except ValidationError as ev:
            errors[i] = ev.messages
    if errors:
        raise ValidationError(errors)


@inlineCallbacks
def _embedded_document_io_validate(field, value):
    return _io_validate_data_proxy(value.schema, value._data)


# Must be a dict of list !
PER_CLASS_IO_VALIDATORS = {
    ReferenceField: [_reference_io_validate],
    ListField: [_list_io_validate],
    EmbeddedField: [_embedded_document_io_validate]
}


def _io_validate_patch_schema(schema):
    """Add default io validators to the given schema
    """
    for field in schema.fields.values():
        io_validate = field.io_validate
        if not io_validate:
            field.io_validate = []
        else:
            if hasattr(io_validate, '__iter__'):
                field.io_validate = list(io_validate)
            else:
                field.io_validate = [io_validate]
        for cls, validators in PER_CLASS_IO_VALIDATORS.items():
            if isinstance(field, cls):
                field.io_validate += validators
