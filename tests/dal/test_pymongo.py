import pytest
from datetime import datetime
from functools import namedtuple
import pymongo
from pymongo import MongoClient

from ..common import BaseTest, get_pymongo_version

from umongo import Document, fields, exceptions


# Check if the required dependancies are met to run this driver's tests
major, minor, _ = get_pymongo_version()
if int(major) != 3 or int(minor) < 2:
    dep_error = "pymongo driver requires pymongo>=3.2.0"
else:
    dep_error = None

if not dep_error:  # Make sure the module is valid by importing it
    from umongo.dal import pymongo


@pytest.fixture
def db():
    return MongoClient().umongo_test


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

    Teacher.collection.drop()
    Course.collection.drop()
    Student.collection.drop()

    return namedtuple('Mapping', ('Teacher', 'Course', 'Student'))(Teacher, Course, Student)


@pytest.mark.skipif(dep_error is not None, reason=dep_error)
class TestPymongo(BaseTest):

    def test_create(self, classroom_model):
        Student = classroom_model.Student
        john = Student(name='John Doe', birthday=datetime(1995, 12, 12))
        john.commit()
        assert john.to_mongo() == {
            '_id': john.id,
            'name': 'John Doe',
            'birthday': datetime(1995, 12, 12)
        }


        john2 = Student.find_one(john.id)
        assert john2._data == john._data

    def test_update(self, classroom_model):
        Student = classroom_model.Student
        john = Student(name='John Doe', birthday=datetime(1995, 12, 12))
        john.commit()
        john.name = 'William Doe'
        assert john.to_mongo(update=True) == {'$set': {'name': 'William Doe'}}
        john.commit()
        assert john.to_mongo(update=True) == None
        john2 = Student.find_one(john.id)
        assert john2._data == john._data

    def test_delete(self, classroom_model):
        Student = classroom_model.Student
        Student.collection.drop()
        john = Student(name='John Doe', birthday=datetime(1995, 12, 12))
        john.commit()
        assert Student.collection.find().count() == 1
        john.delete()
        assert Student.collection.find().count() == 0
        with pytest.raises(exceptions.DeleteError):
           john.delete()

    def test_reload(self, classroom_model):
        Student = classroom_model.Student
        john = Student(name='John Doe', birthday=datetime(1995, 12, 12))
        with pytest.raises(exceptions.NotCreatedError):
            john.reload()
        john.commit()
        john2 = Student.find_one(john.id)
        john2.name = 'William Doe'
        john2.commit()
        john.reload()
        assert john.name == 'William Doe'


    def test_cusor(self, classroom_model):
        Student = classroom_model.Student
        Student.collection.drop()
        for i in range(10):
            Student(name='student-%s' % i).commit()
        cursor = Student.find(limit=5, skip=6)
        assert cursor.count() == 10
        assert cursor.count(with_limit_and_skip=True) == 4
        names = []
        for elem in cursor:
            assert isinstance(elem, Student)
            names.append(elem.name)
        assert sorted(names) == ['student-%s' % i for i in range(6, 10)]

        # Make sure this kind of notation doesn't create new cursor
        cursor = Student.find()
        cursor_limit = cursor.limit(5)
        cursor_skip = cursor.skip(6)
        assert cursor is cursor_limit is cursor_skip

    def test_classroom(self, classroom_model):
        student = classroom_model.Student(name='Marty McFly', birthday=datetime(1968, 6, 9))
        student.commit()
        teacher = classroom_model.Teacher(name='M. Strickland')
        teacher.commit()
        course = classroom_model.Course(name='Overboard 101', teacher=teacher)
        course.commit()
        assert student.courses == []
        student.courses.append(course)
        student.commit()
        assert student.to_mongo() == {
            '_id': student.pk,
            'name': 'Marty McFly',
            'birthday': datetime(1968, 6, 9),
            'courses': [course.pk]
        }
