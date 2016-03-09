from datetime import datetime

from ..fixtures import pymongo_db, classroom_model
from ..common import BaseTest

from umongo import Document, Schema, fields


class TestPymongo(BaseTest):

    def test_create(self, pymongo_db):

        class Student(Document):
            class Schema(Schema):
                name = fields.StrField(required=True)
                birthday = fields.DateTimeField()

            class Config:
                collection = pymongo_db.student

        john = Student(name='John Doe', birthday=datetime(1995, 12, 12))
        john.commit()
        john.to_mongo() == {'_id': john.data.id, 'name': 'John Doe', 'birthday': datetime(1995, 12, 12)}


        john2 = Student.find_one(john.data.id)
        assert john2.data == john.data

    def test_update(self, pymongo_db):

        class Student(Document):
            class Schema(Schema):
                name = fields.StrField(required=True)
                birthday = fields.DateTimeField()

            class Config:
                collection = pymongo_db.student

        john = Student(name='John Doe', birthday=datetime(1995, 12, 12)).commit()
        john.data.name = 'William Doe'
        john.to_mongo(update=True) == {'name': 'William Doe'}
        john.commit()
        john.to_mongo(update=True) == {}
        john2 = Student.find_one(john.data.id)
        assert john2.data == john.data

    def test_reload(self, pymongo_db):

        class Student(Document):
            class Schema(Schema):
                name = fields.StrField(required=True)
                birthday = fields.DateTimeField()

            class Config:
                collection = pymongo_db.student

        john = Student(name='John Doe', birthday=datetime(1995, 12, 12))
        john.commit()
        john2 = Student.find_one(john.data.id)
        john2.data.name = 'William Doe'
        john2.commit()
        john.reload()
        assert john.data.name == 'William Doe'

    def test_cusor(self, pymongo_db):

        class Student(Document):
            class Schema(Schema):
                name = fields.StrField(required=True)
                birthday = fields.DateTimeField()

            class Config:
                collection = pymongo_db.student

        Student.collection.drop()

        for i in range(10):
            Student(name='student-%s' % i).commit()
        cursor = Student.find(limit=5, skip=6)
        assert cursor.count() == 10
        assert cursor.count(with_limit_and_skip=True) == 4
        names = []
        for elem in cursor:
            assert isinstance(elem, Student)
            names.append(elem.data.name)
        assert sorted(names) == ['student-%s' % i for i in range(6, 10)]

    def test_classroom(self, classroom_model):
        student = classroom_model.Student(name='Marty McFly', birthday=datetime(1968, 6, 9)).commit()
        teacher = classroom_model.Teacher(name='M. Strickland').commit()
        course = classroom_model.Course(name='Overboard 101', teacher=teacher).commit()
        assert student.data.courses == []
        student.data.courses.append(course)
        student.commit()
        student.to_mongo() == {
            '_id': student.pk,
            'name': 'Marty McFly',
            'birthday': datetime(1968, 6, 9),
            'courses': [course.pk]
        }
