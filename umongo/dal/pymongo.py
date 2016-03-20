from pymongo.collection import Collection
from pymongo.cursor import Cursor

from ..abstract import AbstractDal
from ..data_proxy import DataProxy, missing
from ..data_objects import Reference
from ..exceptions import NotCreatedError, UpdateError, DeleteError, ValidationError
from ..fields import ReferenceField, ListField, EmbeddedField


class WrappedCursor(Cursor):

    __slots__ = ('raw_cursor', 'document_cls')

    def __init__(self, document_cls, cursor, *args, **kwargs):
        # Such a cunning plan my lord !
        # We inherit from Cursor but don't call it __init__ because
        # we act as a proxy to the underlying raw_cursor
        WrappedCursor.raw_cursor.__set__(self, cursor)
        WrappedCursor.document_cls.__set__(self, document_cls)

    def __getattr__(self, name):
        return getattr(self.raw_cursor, name)

    def __setattr__(self, name, value):
        return setattr(self.raw_cursor, name, value)

    def __next__(self):
        elem = next(self.raw_cursor)
        return self.document_cls.build_from_mongo(elem)

    def __iter__(self):
        for elem in self.raw_cursor:
            yield self.document_cls.build_from_mongo(elem)


class PyMongoDal(AbstractDal):

    @staticmethod
    def is_compatible_with(collection):
        return isinstance(collection, Collection)

    @staticmethod
    def io_validate_patch_schema(schema):
        _io_validate_patch_schema(schema)

    def reload(self):
        ret = self.collection.find_one(self.pk)
        if ret is None:
            raise NotCreatedError("Document doesn't exists in database")
        self._data = DataProxy(self.schema)
        self._data.from_mongo(ret)

    def commit(self, io_validate_all=False):
        self.io_validate(validate_all=io_validate_all)
        payload = self._data.to_mongo(update=self.created)
        if self.created:
            if payload:
                ret = self.collection.update_one(
                    {'_id': self._data.get_by_mongo_name('_id')}, payload)
                if ret.modified_count != 1:
                    raise UpdateError(ret.raw_result)
        else:
            ret = self.collection.insert_one(payload)
            # TODO: check ret ?
            self._data.set_by_mongo_name('_id', ret.inserted_id)
            self.created = True
        self._data.clear_modified()

    def delete(self):
        ret = self.collection.delete_one({'_id': self.pk})
        if ret.deleted_count != 1:
            raise DeleteError(ret.raw_result)

    def io_validate(self, validate_all=False):
        if validate_all:
            _io_validate_data_proxy(self.schema, self._data)
        else:
            _io_validate_data_proxy(
                self.schema, self._data, partial=self._data.get_modified_fields())

    @classmethod
    def find_one(cls, *args, **kwargs):
        ret = cls.collection.find_one(*args, **kwargs)
        if ret is not None:
            ret = cls.build_from_mongo(ret)
        return ret

    @classmethod
    def find(cls, *args, **kwargs):
        raw_cursor = cls.collection.find(*args, **kwargs)
        return WrappedCursor(cls, raw_cursor)


# Run multiple validators and collect all errors in one
def _run_validators(validators, field, value):
    if not hasattr(validators, '__iter__'):
        validators(field, value)
    else:
        errors = []
        for validator in validators:
            try:
                validator(field, value)
            except ValidationError as ve:
                errors.extend(ve.messages)
        if errors:
            raise ValidationError(errors)


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
                    _run_validators(field.io_validate, field, value)
        except ValidationError as ve:
            errors[name] = ve.messages
    if errors:
        raise ValidationError(errors)


def _reference_io_validate(field, value):
    value.io_fetch(no_data=True)


def _list_io_validate(field, value):
    errors = {}
    validators = field.container.io_validate
    if not validators:
        return
    for i, e in enumerate(value):
        try:
            _run_validators(validators, field.container, e)
        except ValidationError as ev:
            errors[i] = ev.messages
    if errors:
        raise ValidationError(errors)


def _embedded_document_io_validate(field, value):
    _io_validate_data_proxy(value.schema, value._data)


def _io_validate_patch_schema(schema):
    """Add default io validators to the given schema
    """

    def patch_field(field):
        validators = field.io_validate
        if not validators:
            field.io_validate = []
        else:
            if hasattr(validators, '__iter__'):
                field.io_validate = list(validators)
            else:
                field.io_validate = [validators]
        if isinstance(field, ListField):
            field.io_validate.append(_list_io_validate)
            patch_field(field.container)
        if isinstance(field, ReferenceField):
            field.io_validate.append(_reference_io_validate)
            field.reference_cls = PyMongoReference
        if isinstance(field, EmbeddedField):
            field.io_validate.append(_embedded_document_io_validate)
            _io_validate_patch_schema(field.schema)

    for field in schema.fields.values():
        patch_field(field)


class PyMongoReference(Reference):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._document = None

    def io_fetch(self, no_data=False):
        if not self._document:
            if self.pk is None:
                raise ReferenceError('Cannot retrieve a None Reference')
            self._document = self.document_cls.find_one(self.pk)
            if not self._document:
                raise ValidationError(
                    'Reference not found for document %s.' % self.document_cls.__name__)
        return self._document
