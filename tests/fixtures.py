import pytest
import pymongo


@pytest.fixture
def db():
    return pymongo.MongoClient().umongo_test


@pytest.fixture
def classroom_model(db):
    pass

    # class Teacher(Document):
    #     id = fields.ObjectId(dump_only=True, attribute='_id')
    #     name = fields.Str(required=True)

    #     class Config:
    #         collection = db.teacher

    # class Course(Document):
    #     id = fields.ObjectId(dump_only=True, attribute='_id')
    #     name = fields.Str(required=True)
    #     teacher = fields.Reference(Teacher, required=True)

    #     class Config:
    #         collection = db.course

    # class Student(Document):
    #     id = fields.ObjectId(dump_only=True, attribute='_id')
    #     name = fields.Str(required=True)
    #     birthday = fields.DateTime()
    #     courses = fields.List(fields.Reference(Course))

    #     class Config:
    #         collection = db.student

    # class Mapping:
    #     teacher = Teacher
    #     course = Course
    #     student = Student

    # return Mapping
