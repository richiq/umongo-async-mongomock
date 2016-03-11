import pytest
import asyncio
from datetime import datetime
from functools import namedtuple

# Check if the required dependancies are met to run this driver's tests
try:
    from motor.motor_asyncio import AsyncIOMotorClient
except ImportError as e:
    dep_error = str(e)
else:
    dep_error = None

from ..common import BaseTest

from umongo import Document, Schema, fields

if not dep_error:  # Make sure the module is valid by importing it
    from umongo.dal import motor_asyncio


@pytest.fixture
def db():
    return AsyncIOMotorClient().umongo_test


@pytest.fixture
def classroom_model(db):

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

    loop = asyncio.get_event_loop()
    loop.set_debug(True)

    @asyncio.coroutine
    def clean_db():
        yield from Teacher.collection.drop()
        yield from Course.collection.drop()
        yield from Student.collection.drop()

    loop.run_until_complete(clean_db())

    return namedtuple('Mapping', ('Teacher', 'Course', 'Student'))(Teacher, Course, Student)


@pytest.fixture
def loop():
    return asyncio.get_event_loop()


@pytest.mark.skipif(dep_error is not None, reason=dep_error)
class TestMotorAsyncio(BaseTest):

    def test_create(self, loop, db):

        @asyncio.coroutine
        def do_test():
            class Student(Document):

                class Schema(Schema):
                    name = fields.StrField(required=True)
                    birthday = fields.DateTimeField()

                class Config:
                    collection = db.student

            john = Student(name='John Doe', birthday=datetime(1995, 12, 12))
            yield from john.commit()
            assert john.to_mongo() == {
                '_id': john.data.id,
                'name': 'John Doe',
                'birthday': datetime(1995, 12, 12)
            }

            john2 = yield from Student.find_one(john.data.id)
            assert john2.data == john.data

        loop.run_until_complete(do_test())

    def test_update(self, loop, db):

        @asyncio.coroutine
        def do_test():

            class Student(Document):

                class Schema(Schema):
                    name = fields.StrField(required=True)
                    birthday = fields.DateTimeField()

                class Config:
                    collection = db.student

            john = Student(name='John Doe', birthday=datetime(1995, 12, 12))
            yield from john.commit()
            john.data.name = 'William Doe'
            assert john.to_mongo(update=True) == {'$set': {'name': 'William Doe'}}
            yield from john.commit()
            assert john.to_mongo(update=True) == None
            john2 = yield from Student.find_one(john.data.id)
            assert john2.data == john.data

        loop.run_until_complete(do_test())

    def test_reload(self, loop, db):

        @asyncio.coroutine
        def do_test():

            class Student(Document):

                class Schema(Schema):
                    name = fields.StrField(required=True)
                    birthday = fields.DateTimeField()

                class Config:
                    collection = db.student

            john = Student(name='John Doe', birthday=datetime(1995, 12, 12))
            yield from john.commit()
            john2 = yield from Student.find_one(john.data.id)
            john2.data.name = 'William Doe'
            yield from john2.commit()
            yield from john.reload()
            assert john.data.name == 'William Doe'

        loop.run_until_complete(do_test())

    @pytest.mark.xfail
    def test_cusor(self, loop, db):

        @asyncio.coroutine
        def do_test():

            class Student(Document):

                class Schema(Schema):
                    name = fields.StrField(required=True)
                    birthday = fields.DateTimeField()

                class Config:
                    collection = db.student

            Student.collection.drop()

            for i in range(10):
                yield from Student(name='student-%s' % i).commit()
            cursor = yield from Student.find(limit=5, skip=6)
            assert cursor.count() == 10
            assert cursor.count(with_limit_and_skip=True) == 4
            names = []
            for elem in cursor:
                assert isinstance(elem, Student)
                names.append(elem.data.name)
            assert sorted(names) == ['student-%s' % i for i in range(6, 10)]

        loop.run_until_complete(do_test())

    def test_classroom(self, loop, classroom_model):

        @asyncio.coroutine
        def do_test():

            student = classroom_model.Student(name='Marty McFly', birthday=datetime(1968, 6, 9))
            yield from student.commit()
            teacher = classroom_model.Teacher(name='M. Strickland')
            yield from teacher.commit()
            course = classroom_model.Course(name='Overboard 101', teacher=teacher)
            yield from course.commit()
            assert student.data.courses == []
            student.data.courses.append(course)
            yield from student.commit()
            assert student.to_mongo() == {
                '_id': student.pk,
                'name': 'Marty McFly',
                'birthday': datetime(1968, 6, 9),
                'courses': [course.pk]
            }

        loop.run_until_complete(do_test())
