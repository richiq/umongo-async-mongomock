import pytest
from functools import namedtuple
from collections import deque
from bson import ObjectId

from umongo import Document, Schema, fields
from umongo.abstract import AbstractDal
from umongo.instance import Instance


@pytest.fixture
def instance(db):
    # `db` should be a fixture provided by the current dal testbench
    return Instance(db)


@pytest.fixture
def classroom_model(instance):

    @instance.register
    class Teacher(Document):
        name = fields.StrField(required=True)

    @instance.register
    class Course(Document):
        name = fields.StrField(required=True)
        teacher = fields.ReferenceField(Teacher, required=True)

    @instance.register
    class Student(Document):
        name = fields.StrField(required=True)
        birthday = fields.DateTimeField()
        courses = fields.ListField(fields.ReferenceField(Course))

        class Meta:
            allow_inheritance = True

    return namedtuple('Mapping', ('Teacher', 'Course', 'Student'))(Teacher, Course, Student)


# @pytest.fixture
# def moked_lazy_loader(dal_moke):
#     return lazy_loader_factory(lambda: dal_moke)
