import pytest
from functools import namedtuple
from collections import deque
from bson import ObjectId

from umongo import Document, Schema, fields, dal
from umongo.abstract import AbstractDal
from umongo.dal import register_dal, unregister_dal


class BaseMokedDal(AbstractDal):

    @staticmethod
    def is_compatible_with(collection):
        return True

    @staticmethod
    def io_validate_patch_schema(schema):
        pass

    def reload(self):
        pass

    def commit(self):
        payload = self._data.to_mongo(update=self.created)
        if not self.created:
            if not self._data.get_by_mongo_name('_id'):
                self._data.set_by_mongo_name('_id', ObjectId())
            self.created = True
        self._data.clear_modified()

    def delete(self):
        pass

    def find_one(self, *args, **kwargs):
        pass

    def find(self, *args, **kwargs):
        pass


class CallTracerMoke:

    def __init__(self):
        self.__callbacks = deque()
        self.__used_callbacks = []

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        if not exc_type and self.__callbacks:
            msg = "Used callbacks:\n"
            for name, callback in self.__used_callbacks:
                msg += " - %s (%s)\n" % (name, callback)
            msg += "\nRemaining callbacks:\n"
            for name, callback in self.__callbacks:
                msg += " - %s (%s)\n" % (name, callback)            
            raise RuntimeError(msg)

    def push_callback(self, func_name, callback=None, to_return=None):
        assert callback is None or to_return is None, 'Cannot both set `to_return` and `callback`'
        if not callback:
            callback = lambda *args, **kwargs: to_return
        self.__callbacks.append((func_name, callback))

    def remaining_callbacks(self):
        return bool(self.__callbacks)

    def __getattr__(self, name):
        try:
            func_name, callback = self.__callbacks.popleft()
        except IndexError:
            raise RuntimeError('Trying to call `%s`, but no more callback registered' % name)
        if name != func_name:
            raise RuntimeError('Expecting `%s` to be called, got `%s`' % (func_name, name))
        self.__used_callbacks.append((func_name, callback))
        return callback


@pytest.fixture
def dal_moke(request, collection_moke):

    # Really simple DAL: just proxy to the collection_moke for everything
    class MokedDal(BaseMokedDal):

        @staticmethod
        def is_compatible_with(collection):
            return collection is collection_moke

        def reload(self):
            self._pass_to_collection("reload", self)

        def commit(self):
            super().commit()
            self._pass_to_collection("commit", self)

        def delete(self):
            self._pass_to_collection("delete", self)

        def io_validate(self, *args, **kwargs):
            self._pass_to_collection("io_validate", self, *args, **kwargs)

        @classmethod
        def find_one(cls, *args, **kwargs):
            cls._pass_to_collection("find_one", cls, *args, **kwargs)

        @classmethod
        def find(cls, *args, **kwargs):
            cls._pass_to_collection("find", cls, *args, **kwargs)

        @classmethod
        def _pass_to_collection(cls, name, doc, *args, **kwargs):
            return getattr(cls.collection, name)(doc, *args, **kwargs)

    register_dal(MokedDal)
    request.addfinalizer(lambda: unregister_dal(MokedDal))
    return MokedDal


@pytest.fixture
def collection_moke(request, name='my_moked_col'):

    class MokedCollection(CallTracerMoke):

        def __init__(self, name):
            self.name = name
            super().__init__()
            self.__callbacks = deque()

    my_collection_moke = MokedCollection(name)
    dal_moke(request, my_collection_moke)
    return my_collection_moke


@pytest.fixture
def classroom_model(db):
    # `db` should be a fixture provided by the current dal testbench

    class Teacher(Document):

        class Schema(Schema):
            name = fields.StrField(required=True)

        class Config:
            register_document = False
            collection = db.teacher

    class Course(Document):

        class Schema(Schema):
            name = fields.StrField(required=True)
            teacher = fields.ReferenceField(Teacher, required=True)

        class Config:
            register_document = False
            collection = db.course

    class Student(Document):

        class Schema(Schema):
            name = fields.StrField(required=True)
            birthday = fields.DateTimeField()
            courses = fields.ListField(fields.ReferenceField(Course))

        class Config:
            register_document = False
            collection = db.student

    Teacher.collection.drop()
    Course.collection.drop()
    Student.collection.drop()

    return namedtuple('Mapping', ('Teacher', 'Course', 'Student'))(Teacher, Course, Student)
