import pytest
from functools import namedtuple

from umongo import Document, Schema, fields


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

    Teacher.collection.drop()
    Course.collection.drop()
    Student.collection.drop()

    return namedtuple('Mapping', ('Teacher', 'Course', 'Student'))(Teacher, Course, Student)
