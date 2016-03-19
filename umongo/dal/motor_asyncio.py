import asyncio
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorCursor

from ..abstract import AbstractDal
from ..data_proxy import DataProxy, missing
from ..data_objects import Reference
from ..exceptions import NotCreatedError, UpdateError, ValidationError
from ..fields import ReferenceField, ListField, EmbeddedField


class WrappedCursor(AsyncIOMotorCursor):

    __slots__ = ('raw_cursor', 'document_cls')

    def __init__(self, document_cls, cursor):
        # Such a cunning plan my lord !
        # We inherit from Cursor but don't call it __init__ because
        # we act as a proxy to the underlying raw_cursor
        WrappedCursor.raw_cursor.__set__(self, cursor)
        WrappedCursor.document_cls.__set__(self, document_cls)

    def __getattr__(self, name):
        return getattr(self.raw_cursor, name)

    def __setattr__(self, name, value):
        return setattr(self.raw_cursor, name, value)

    def clone(self):
        return WrappedCursor(self.document_cls, self.raw_cursor.clone())

    def next_object(self):
        raw = self.raw_cursor.next_object()
        return self.document_cls.build_from_mongo(raw)

    def each(self, callback):
        def wrapped_callback(result, error):
            if not error and result is not None:
                result = self.document_cls.build_from_mongo(result)
            return callback(result, error)
        return self.raw_cursor.each(wrapped_callback)

    def to_list(self, length, callback=None):
        raw_future = self.raw_cursor.to_list(length, callback=callback)
        cooked_future = asyncio.Future()
        builder = self.document_cls.build_from_mongo

        def on_raw_done(fut):
            cooked_future.set_result([builder(e) for e in fut.result()])

        raw_future.add_done_callback(on_raw_done)
        return cooked_future


class MotorAsyncIODal(AbstractDal):

    @staticmethod
    def is_compatible_with(collection):
        return isinstance(collection, AsyncIOMotorCollection)

    @staticmethod
    def io_validate_patch_schema(schema):
        _io_validate_patch_schema(schema)

    def reload(self):
        ret = yield from self.collection.find_one(self.pk)
        if ret is None:
            raise NotCreatedError("Document doesn't exists in database")
        self._data = DataProxy(self.schema)
        self._data.from_mongo(ret)

    def commit(self, io_validate_all=False):
        yield from self.io_validate(validate_all=io_validate_all)
        payload = self._data.to_mongo(update=self.created)
        if self.created:
            if payload:
                ret = yield from self.collection.update(
                    {'_id': self._data.get_by_mongo_name('_id')}, payload)
                if ret.get('nModified') != 1:
                    raise UpdateError(ret.raw_result)
        else:
            ret = yield from self.collection.insert(payload)
            # TODO: check ret ?
            self._data.set_by_mongo_name('_id', ret)
            self.created = True
        self._data.clear_modified()

    def delete(self):
        raise NotImplementedError()

    def io_validate(self, validate_all=False):
        if validate_all:
            return _io_validate_data_proxy(self.schema, self._data)
        else:
            return _io_validate_data_proxy(
                self.schema, self._data, partial=self._data.get_modified_fields())

    @classmethod
    def find_one(cls, *args, **kwargs):
        ret = yield from cls.collection.find_one(*args, **kwargs)
        if ret is not None:
            ret = cls.build_from_mongo(ret)
        return ret

    @classmethod
    def find(cls, *args, **kwargs):
        return WrappedCursor(cls, cls.collection.find(*args, **kwargs))


# Run multiple validators and collect all errors in one
@asyncio.coroutine
def _run_validators(validators, field, value):
    errors = []
    tasks = [validator(field, value) for validator in validators]
    results = yield from asyncio.gather(*tasks, return_exceptions=True)
    for i, res in enumerate(results):
        if isinstance(res, ValidationError):
            errors.extend(res.messages)
        elif res:
            raise res
    if errors:
        raise ValidationError(errors)


def _io_validate_data_proxy(schema, data_proxy, partial=None):
    errors = {}
    tasks = []
    tasks_field_name = []
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
                    tasks.append(_run_validators(field.io_validate, field, value))
                    tasks_field_name.append(name)
        except ValidationError as ve:
            errors[name] = ve.messages
    results = yield from asyncio.gather(*tasks, return_exceptions=True)
    for i, res in enumerate(results):
        if isinstance(res, ValidationError):
            errors[tasks_field_name[i]] = res.messages
        elif res:
            raise res
    if errors:
        raise ValidationError(errors)


@asyncio.coroutine
def _reference_io_validate(field, value):
    yield from value.io_fetch(no_data=True)


@asyncio.coroutine
def _list_io_validate(field, value):
    validators = field.container.io_validate
    if not validators or not value:
        return
    tasks = [_run_validators(validators, field.container, e) for e in value]
    results = yield from asyncio.gather(*tasks, return_exceptions=True)
    errors = {}
    for i, res in enumerate(results):
        if isinstance(res, ValidationError):
            errors[i] = res.messages
        elif res:
            raise res
    if errors:
        raise ValidationError(errors)


@asyncio.coroutine
def _embedded_document_io_validate(field, value):
    yield from _io_validate_data_proxy(value.schema, value._data)


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
            field.io_validate = [v if asyncio.iscoroutinefunction(v) else asyncio.coroutine(v)
                                 for v in validators]
        if isinstance(field, ListField):
            field.io_validate.append(_list_io_validate)
            patch_field(field.container)
        if isinstance(field, ReferenceField):
            field.io_validate.append(_reference_io_validate)
            field.reference_cls = MotorAsyncIOReference
        if isinstance(field, EmbeddedField):
            field.io_validate.append(_embedded_document_io_validate)
            _io_validate_patch_schema(field.schema)

    for field in schema.fields.values():
        patch_field(field)


class MotorAsyncIOReference(Reference):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._document = None

    def io_fetch(self, no_data=False):
        if not self._document:
            if self.pk is None:
                raise ReferenceError('Cannot retrieve a None Reference')
            self._document = yield from self.document_cls.find_one(self.pk)
            if not self._document:
                raise ValidationError(
                    'Reference not found for document %s.' % self.document_cls.__name__)
        return self._document
