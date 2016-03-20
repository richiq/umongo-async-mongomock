from txmongo.collection import Collection
from twisted.internet.defer import inlineCallbacks, Deferred, DeferredList, returnValue

from ..abstract import AbstractDal
from ..data_proxy import DataProxy, missing
from ..data_objects import Reference
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
        yield self.io_validate(validate_all=io_validate_all)
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


def _errback_factory(errors, field=None):

    def errback(err):
        if isinstance(err.value, ValidationError):
            if field:
                errors[field] = err.value.messages
            else:
                errors.extend(err.value.messages)
        else:
            raise err.value

    return errback


# Run multiple validators and collect all errors in one
@inlineCallbacks
def _run_validators(validators, field, value):
    errors = []
    defers = []
    for validator in validators:
        defer = validator(field, value)
        assert isinstance(defer, Deferred), 'io_validate functions must return a Deferred'
        defer.addErrback(_errback_factory(errors))
        defers.append(defer)
    yield DeferredList(defers)
    if errors:
        raise ValidationError(errors)


@inlineCallbacks
def _io_validate_data_proxy(schema, data_proxy, partial=None):
    errors = {}
    defers = []
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
                    defer = _run_validators(field.io_validate, field, value)
                    defer.addErrback(_errback_factory(errors, name))
                    defers.append(defer)
        except ValidationError as ve:
            errors[name] = ve.messages
    yield DeferredList(defers)
    if errors:
        raise ValidationError(errors)


def _reference_io_validate(field, value):
    return value.io_fetch(no_data=True)


@inlineCallbacks
def _list_io_validate(field, value):
    validators = field.container.io_validate
    if not validators or not value:
        return
    errors = {}
    defers = []
    for i, e in enumerate(value):
        defer = _run_validators(validators, field.container, e)
        defer.addErrback(_errback_factory(errors, i))
        defers.append(defer)
    yield DeferredList(defers)
    if errors:
        raise ValidationError(errors)


def _embedded_document_io_validate(field, value):
    return _io_validate_data_proxy(value.schema, value._data)


def _io_validate_patch_schema(schema):
    """Add default io validators to the given schema
    """

    def patch_field(field):
        validators = field.io_validate
        if not validators:
            field.io_validate = []
        else:
            if hasattr(validators, '__iter__'):
                validators = list(validators)
            else:
                validators = [validators]
            field.io_validate = validators
        if isinstance(field, ListField):
            field.io_validate.append(_list_io_validate)
            patch_field(field.container)
        if isinstance(field, ReferenceField):
            field.io_validate.append(_reference_io_validate)
            field.reference_cls = TxMongoReference
        if isinstance(field, EmbeddedField):
            field.io_validate.append(_embedded_document_io_validate)
            _io_validate_patch_schema(field.schema)

    for field in schema.fields.values():
        patch_field(field)


class TxMongoReference(Reference):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._document = None

    @inlineCallbacks
    def io_fetch(self, no_data=False):
        if not self._document:
            if self.pk is None:
                raise ReferenceError('Cannot retrieve a None Reference')
            self._document = yield self.document_cls.find_one(self.pk)
            if not self._document:
                raise ValidationError(
                    'Reference not found for document %s.' % self.document_cls.__name__)
        returnValue(self._document)
