from datetime import datetime

from .fixtures import db, classroom_model
from umongo import *


class TestBase:

    def test_create(self, db):

        class Student(Document):
            id = fields.ObjectId(dump_only=True, attribute='_id')
            name = fields.Str(required=True)
            birthday = fields.DateTime()

            class Config:
                collection = db.student

        john = Student(name='John Doe', birthday=datetime(1995, 12, 12))
        john.save()
        john.to_mongo() == {'_id': john.data['_id'], 'name': 'John Doe', 'birthday': datetime(1995, 12, 12)}
        john2 = Student.find_one(john.id)
        assert john2.data == john.data

    def test_update(self, db):

        class Student(Document):
            id = fields.ObjectId(dump_only=True, attribute='_id')
            name = fields.Str(required=True)
            birthday = fields.DateTime()

            class Config:
                collection = db.student

        john = Student(name='John Doe', birthday=datetime(1995, 12, 12))
        john.save()
        john.name = 'William Doe'
        john.to_mongo_update() == {'$set': {'name': 'William Doe'}}
        john.save()
        with pytest.raises():  # TODO: complete me !
            john.to_mongo_update()
        john2 = Student.find_one(john.id)
        assert john2.data == john.data

    def test_reset(self, db):

        class Student(Document):
            id = fields.ObjectId(dump_only=True, attribute='_id')
            name = fields.Str(required=True)
            birthday = fields.DateTime()

            class Config:
                collection = db.student

        john = Student(name='John Doe', birthday=datetime(1995, 12, 12))
        john.save()
        john.name = 'William Doe'
        john.reset()
        assert john.name == 'John Doe'
        with pytest.raises():  # TODO: complete me !
            john.to_mongo_update()

    def test_reload(self, db):

        class Student(Document):
            id = fields.ObjectId(dump_only=True, attribute='_id')
            name = fields.Str(required=True)
            birthday = fields.DateTime()

            class Config:
                collection = db.student

        john = Student(name='John Doe', birthday=datetime(1995, 12, 12))
        john.save()
        john2 = Student.find_one(john.id)
        john2.name = 'William Doe'
        john2.save()
        john.reload()
        assert john.name == 'William Doe'

    # def test_classroom(classroom_model):
    #     student = classroom_model.Student(name='Marty McFly', birthday=datetime(1968, 6, 9)).save()
    #     teacher = classroom_model.Student(name='M. Strickland', ).save()
    #     course = classroom_model.Course(name='Overboard 101', teacher=teacher).save()
    #     assert student.courses == []
    #     student.courses.append(course)
    #     student.save()
    #     student.to_mongo() == {
    #         '_id': student.data['_id'],
    #         'name': 'Marty McFly',
    #         'birthday': datetime(1968, 6, 9),
    #         'courses': [course.data['_id']]
    #     }
