import pytest
import asyncio
from datetime import datetime
from functools import namedtuple
from bson import ObjectId

# Check if the required dependancies are met to run this driver's tests
try:
    from motor.motor_asyncio import AsyncIOMotorClient
except ImportError as e:
    dep_error = str(e)
else:
    dep_error = None

from ..common import BaseTest

from umongo import Document, fields, exceptions, Reference

if not dep_error:  # Make sure the module is valid by importing it
    from umongo.dal import motor_asyncio


@pytest.fixture
def db():
    return AsyncIOMotorClient().umongo_test


@pytest.fixture
def classroom_model(db):

    class Teacher(Document):
        name = fields.StrField(required=True)

        class Config:
            register_document = False
            collection = db.teacher

    class Course(Document):
        name = fields.StrField(required=True)
        teacher = fields.ReferenceField(Teacher, required=True)

        class Config:
            register_document = False
            collection = db.course

    class Student(Document):
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

    def test_create(self, loop, classroom_model):
        Student = classroom_model.Student

        @asyncio.coroutine
        def do_test():
            john = Student(name='John Doe', birthday=datetime(1995, 12, 12))
            yield from john.commit()
            assert john.to_mongo() == {
                '_id': john.id,
                'name': 'John Doe',
                'birthday': datetime(1995, 12, 12)
            }

            john2 = yield from Student.find_one(john.id)
            assert john2._data == john._data

        loop.run_until_complete(do_test())

    def test_update(self, loop, classroom_model):
        Student = classroom_model.Student

        @asyncio.coroutine
        def do_test():
            john = Student(name='John Doe', birthday=datetime(1995, 12, 12))
            yield from john.commit()
            john.name = 'William Doe'
            assert john.to_mongo(update=True) == {'$set': {'name': 'William Doe'}}
            yield from john.commit()
            assert john.to_mongo(update=True) == None
            john2 = yield from Student.find_one(john.id)
            assert john2._data == john._data

        loop.run_until_complete(do_test())

    def test_delete(self, classroom_model):
        Student = classroom_model.Student

        @asyncio.coroutine
        def do_test():
            yield from db.student.drop()
            john = Student(name='John Doe', birthday=datetime(1995, 12, 12))
            yield from john.commit()
            assert (yield from db.student.find()).count() == 1
            yield from john.delete()
            assert (yield from db.student.find()).count() == 0
            with pytest.raises(exceptions.DeleteError):
               yield from john.delete()

    def test_reload(self, loop, classroom_model):
        Student = classroom_model.Student

        @asyncio.coroutine
        def do_test():
            john = Student(name='John Doe', birthday=datetime(1995, 12, 12))
            with pytest.raises(exceptions.NotCreatedError):
                yield from john.reload()
            yield from john.commit()
            john2 = yield from Student.find_one(john.id)
            john2.name = 'William Doe'
            yield from john2.commit()
            yield from john.reload()
            assert john.name == 'William Doe'

        loop.run_until_complete(do_test())

    def test_cursor(self, loop, classroom_model):
        Student = classroom_model.Student

        @asyncio.coroutine
        def do_test():
            Student.collection.drop()

            for i in range(10):
                yield from Student(name='student-%s' % i).commit()
            cursor = Student.find(limit=5, skip=6)
            count = yield from cursor.count()
            assert count == 10
            count_with_limit_and_skip = yield from cursor.count(with_limit_and_skip=True)
            assert count_with_limit_and_skip == 4

            # Make sure returned documents are wrapped
            names = []
            for elem in (yield from cursor.to_list(length=100)):
                assert isinstance(elem, Student)
                names.append(elem.name)
            assert sorted(names) == ['student-%s' % i for i in range(6, 10)]

            # Try with fetch_next as well
            names = []
            cursor.rewind()
            while (yield from cursor.fetch_next):
                elem = cursor.next_object()
                assert isinstance(elem, Student)
                names.append(elem.name)
            assert sorted(names) == ['student-%s' % i for i in range(6, 10)]

            # Try with each as well
            names = []
            cursor.rewind()
            future = asyncio.Future()

            def callback(result, error):
                if error:
                    future.set_exception(error)
                elif result is None:
                    # Iteration complete
                    future.set_result(names)
                else:
                    names.append(result.name)

            cursor.each(callback=callback)
            yield from future
            assert sorted(names) == ['student-%s' % i for i in range(6, 10)]

            # Make sure this kind of notation doesn't create new cursor
            cursor = Student.find()
            cursor_limit = cursor.limit(5)
            cursor_skip = cursor.skip(6)
            assert cursor is cursor_limit is cursor_skip

            # Test clone&rewind as well
            cursor = Student.find()
            cursor2 = cursor.clone()
            yield from cursor.fetch_next
            yield from cursor2.fetch_next
            cursor_student = cursor.next_object()
            cursor2_student = cursor2.next_object()
            assert cursor_student == cursor2_student

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
            assert student.courses == []
            student.courses.append(course)
            yield from student.commit()
            assert student.to_mongo() == {
                '_id': student.pk,
                'name': 'Marty McFly',
                'birthday': datetime(1968, 6, 9),
                'courses': [course.pk]
            }

        loop.run_until_complete(do_test())

    def test_reference(self, loop, classroom_model):

        @asyncio.coroutine
        def do_test():

            teacher = classroom_model.Teacher(name='M. Strickland')
            yield from teacher.commit()
            course = classroom_model.Course(name='Overboard 101', teacher=teacher)
            yield from course.commit()
            assert isinstance(course.teacher, Reference)
            teacher_fetched = yield from course.teacher.io_fetch()
            assert teacher_fetched == teacher
            # Test bad ref as well
            course.teacher = Reference(classroom_model.Teacher, ObjectId())
            with pytest.raises(exceptions.ValidationError) as exc:
                yield from course.io_validate()
            assert exc.value.messages == {'teacher': ['Reference not found for document Teacher.']}

        loop.run_until_complete(do_test())

    def test_required(self, loop, classroom_model):

        @asyncio.coroutine
        def do_test():

            Student = classroom_model.Student
            student = Student(birthday=datetime(1968, 6, 9))

            with pytest.raises(exceptions.ValidationError) as exc:
                yield from student.io_validate()
            assert exc.value.messages == {'name': ['Missing data for required field.']}

            with pytest.raises(exceptions.ValidationError) as exc:
                yield from student.commit()
            assert exc.value.messages == {'name': ['Missing data for required field.']}

            student.name = 'Marty'
            yield from student.commit()

            # with pytest.raises(exceptions.ValidationError):
            #     Student.build_from_mongo({})

        loop.run_until_complete(do_test())

    def test_io_validate(self, loop, classroom_model):

        @asyncio.coroutine
        def do_test():

            Student = classroom_model.Student

            io_field_value = 'io?'
            io_validate_called = False

            def io_validate(field, value):
                assert field == IOStudent.schema.fields['io_field']
                assert value == io_field_value
                nonlocal io_validate_called
                io_validate_called = True

            class IOStudent(Student):
                io_field = fields.StrField(io_validate=io_validate)

            student = IOStudent(name='Marty', io_field=io_field_value)
            assert not io_validate_called

            yield from student.io_validate()
            assert io_validate_called

        loop.run_until_complete(do_test())

    def test_io_validate_error(self, loop, classroom_model):

        @asyncio.coroutine
        def do_test():

            Student = classroom_model.Student

            def io_validate(field, value):
                raise exceptions.ValidationError('Ho boys !')

            class IOStudent(Student):
                io_field = fields.StrField(io_validate=io_validate)

            student = IOStudent(name='Marty', io_field='io?')
            with pytest.raises(exceptions.ValidationError) as exc:
                yield from student.io_validate()
            assert exc.value.messages == {'io_field': ['Ho boys !']}

        loop.run_until_complete(do_test())

    def test_io_validate_multi_validate(self, loop, classroom_model):

        @asyncio.coroutine
        def do_test():

            Student = classroom_model.Student
            called = []

            future1 = asyncio.Future()
            future2 = asyncio.Future()
            future3 = asyncio.Future()
            future4 = asyncio.Future()

            def io_validate11(field, value):
                called.append(1)
                future1.set_result(None)
                yield from future3
                called.append(4)
                future4.set_result(None)

            def io_validate12(field, value):
                yield from future4
                called.append(5)

            def io_validate21(field, value):
                yield from future2
                called.append(3)
                future3.set_result(None)

            def io_validate22(field, value):
                yield from future1
                called.append(2)
                future2.set_result(None)

            class IOStudent(Student):
                io_field1 = fields.StrField(io_validate=(io_validate11, io_validate12))
                io_field2 = fields.StrField(io_validate=(io_validate21, io_validate22))

            student = IOStudent(name='Marty', io_field1='io1', io_field2='io2')
            yield from student.io_validate()
            assert called == [1, 2, 3, 4, 5]

        loop.run_until_complete(do_test())

    def test_io_validate_list(self, loop, classroom_model):

        @asyncio.coroutine
        def do_test():

            Student = classroom_model.Student
            called = []

            values = [1, 2, 3, 4]
            total = len(values)
            futures = [asyncio.Future() for _ in range(total*2)]

            def io_validate(field, value):
                futures[total - value + 1].set_result(None)
                yield from futures[value]
                called.append(value)

            class IOStudent(Student):
                io_field = fields.ListField(fields.IntField(io_validate=io_validate))

            student = IOStudent(name='Marty', io_field=values)
            yield from student.io_validate()
            assert set(called) == set(values)

        loop.run_until_complete(do_test())
