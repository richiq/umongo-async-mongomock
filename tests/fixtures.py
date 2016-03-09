import pytest
import pymongo
from functools import namedtuple

from umongo import Document, Schema, fields


@pytest.fixture
def pymongo_db():
    return pymongo.MongoClient().umongo_test


@pytest.fixture
def classroom_model(pymongo_db):

    class Teacher(Document):

        class Schema(Schema):
            name = fields.StrField(required=True)

        class Config:
            register_document = False
            collection = pymongo_db.teacher

    class Course(Document):

        class Schema(Schema):
            name = fields.StrField(required=True)
            teacher = fields.ReferenceField(Teacher, required=True)

        class Config:
            register_document = False
            collection = pymongo_db.course

    class Student(Document):

        class Schema(Schema):
            name = fields.StrField(required=True)
            birthday = fields.DateTimeField()
            courses = fields.ListField(fields.ReferenceField(Course))

        class Config:
            register_document = False
            collection = pymongo_db.student

    Teacher.collection.drop()
    Course.collection.drop()
    Student.collection.drop()

    return namedtuple('Mapping', ('Teacher', 'Course', 'Student'))(Teacher, Course, Student)
