import pytest
from functools import namedtuple
from collections import deque

from umongo import Document, Schema, fields, dal
from umongo.dal import register_dal


class BaseMoke:

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
def collection_moke(name='my_moked_col'):

    class CollectionMoke(BaseMoke):

        def __init__(self, name):
            self.name = name
            super().__init__()
            self.__callbacks = deque()

    my_collection_moke = CollectionMoke(name)

    # Really simple DAL: just proxy to the collection for everything
    class DALMoke:

        @staticmethod
        def is_compatible_with(collection):
            return collection is my_collection_moke

        def __getattr__(self, name):

            def caller(doc, *args, **kwargs):
                return getattr(doc.collection, name)(doc, *args, **kwargs)

            return caller

    register_dal(DALMoke())
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
