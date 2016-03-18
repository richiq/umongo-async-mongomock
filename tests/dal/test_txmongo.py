import pytest
from datetime import datetime
from functools import namedtuple, wraps

from ..common import BaseTest, get_pymongo_version

# Check if the required dependancies are met to run this driver's tests
try:
    from txmongo import MongoConnection
    major, minor, _ = get_pymongo_version()
    if major != 3 or minor < 2:
        dep_error = "txmongo requires pymongo>=3.2.0"
except ImportError:
    dep_error = 'Missing txmongo module'
    # Given the test function are generator, we must wrap them into a dummy
    # function that pytest can skip
    def skip_wrapper(f):

        @wraps(f)
        def wrapper(self):
            pass

        return wrapper

    pytest_inlineCallbacks = skip_wrapper
else:
    dep_error = None
    pytest_inlineCallbacks = pytest.inlineCallbacks

from umongo import Document, fields, exceptions


if not dep_error:  # Make sure the module is valid by importing it
    from umongo.dal import txmongo


@pytest.fixture
def db():
    return MongoConnection().umongo_test


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

    pytest.blockon(Teacher.collection.drop())
    pytest.blockon(Course.collection.drop())
    pytest.blockon(Student.collection.drop())

    return namedtuple('Mapping', ('Teacher', 'Course', 'Student'))(Teacher, Course, Student)


@pytest.mark.skipif(dep_error is not None, reason=dep_error)
class TestTxMongo(BaseTest):

    @pytest_inlineCallbacks
    def test_create(self, classroom_model):
        Student = classroom_model.Student
        john = Student(name='John Doe', birthday=datetime(1995, 12, 12))
        yield john.commit()
        assert john.to_mongo() == {
            '_id': john.id,
            'name': 'John Doe',
            'birthday': datetime(1995, 12, 12)
        }

        john2 = yield Student.find_one(john.id)
        assert john2._data == john._data

    @pytest_inlineCallbacks
    def test_update(self, classroom_model):
        Student = classroom_model.Student
        john = Student(name='John Doe', birthday=datetime(1995, 12, 12))
        yield john.commit()
        john.name = 'William Doe'
        assert john.to_mongo(update=True) == {'$set': {'name': 'William Doe'}}
        yield john.commit()
        assert john.to_mongo(update=True) == None
        john2 = yield Student.find_one(john.id)
        assert john2._data == john._data

    @pytest_inlineCallbacks
    def test_delete(self, db):

        class Student(Document):
            name = fields.StrField(required=True)
            birthday = fields.DateTimeField()

            class Config:
                collection = db.student

        yield db.student.drop()
        john = Student(name='John Doe', birthday=datetime(1995, 12, 12))
        yield john.commit()
        students = yield db.student.find()
        assert len(students) == 1
        yield john.delete()
        students = yield db.student.find()
        assert len(students) == 0
        with pytest.raises(exceptions.DeleteError):
           yield john.delete()

    @pytest_inlineCallbacks
    def test_reload(self, classroom_model):
        Student = classroom_model.Student
        john = Student(name='John Doe', birthday=datetime(1995, 12, 12))
        with pytest.raises(exceptions.NotCreatedError):
            yield john.reload()
        yield john.commit()
        john2 = yield Student.find_one(john.id)
        john2.name = 'William Doe'
        yield john2.commit()
        yield john.reload()
        assert john.name == 'William Doe'

    @pytest_inlineCallbacks
    def test_find_no_cursor(self, classroom_model):
        Student = classroom_model.Student
        Student.collection.drop()
        for i in range(10):
            yield Student(name='student-%s' % i).commit()
        results = yield Student.find(limit=5, skip=6)
        assert isinstance(results, list)
        assert len(results) == 4
        names = []
        for elem in results:
            assert isinstance(elem, Student)
            names.append(elem.name)
        assert sorted(names) == ['student-%s' % i for i in range(6, 10)]

    @pytest_inlineCallbacks
    def test_find_with_cursor(self, classroom_model):
        Student = classroom_model.Student
        Student.collection.drop()
        for i in range(10):
            yield Student(name='student-%s' % i).commit()
        batch1, cursor1 = yield Student.find(limit=5, skip=6, cursor=True)
        assert len(batch1) == 4
        batch2, cursor2 = yield cursor1
        assert len(batch2) == 0
        assert cursor2 is None
        names = []
        for elem in batch1:
            assert isinstance(elem, Student)
            names.append(elem.name)
        assert sorted(names) == ['student-%s' % i for i in range(6, 10)]

    @pytest_inlineCallbacks
    def test_classroom(self, classroom_model):
        student = classroom_model.Student(name='Marty McFly', birthday=datetime(1968, 6, 9))
        yield student.commit()
        teacher = classroom_model.Teacher(name='M. Strickland')
        yield teacher.commit()
        course = classroom_model.Course(name='Overboard 101', teacher=teacher)
        yield course.commit()
        assert student.courses == []
        student.courses.append(course)
        yield student.commit()
        assert student.to_mongo() == {
            '_id': student.pk,
            'name': 'Marty McFly',
            'birthday': datetime(1968, 6, 9),
            'courses': [course.pk]
        }
