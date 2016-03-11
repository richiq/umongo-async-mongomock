from datetime import datetime

from .common import BaseTest
from umongo import Document, Schema, fields


class Student(Document):
    class Schema(Schema):
        name = fields.StrField(required=True)
        birthday = fields.DateTimeField()
        gpa = fields.FloatField()


class TestDocument(BaseTest):

    def test_create(self):
        john = Student(name='John Doe', birthday=datetime(1995, 12, 12), gpa=3.0)
        assert john.to_mongo() == {
            'name': 'John Doe',
            'birthday': datetime(1995, 12, 12),
            'gpa': 3.0
        }
        assert john.created is False

    def test_from_mongo(self):
        john = Student.build_from_mongo(data={
            'name': 'John Doe', 'birthday': datetime(1995, 12, 12), 'gpa': 3.0})
        assert john.to_mongo(update=True) is None
        assert john.created is True
        assert john.to_mongo() == {
            'name': 'John Doe',
            'birthday': datetime(1995, 12, 12),
            'gpa': 3.0
        }

    def test_update(self):
        john = Student.build_from_mongo(data={
            'name': 'John Doe', 'birthday': datetime(1995, 12, 12), 'gpa': 3.0})
        john.data.name = 'William Doe'
        john.data.birthday = datetime(1996, 12, 12)
        assert john.to_mongo(update=True) == {
            '$set': {'name': 'William Doe', 'birthday': datetime(1996, 12, 12)}}

    def test_dump(self):
        john = Student.build_from_mongo({
            'name': 'John Doe', 'birthday': datetime(1995, 12, 12), 'gpa': 3.0})
        assert john.dump() == {
            'name': 'John Doe',
            'birthday': '1995-12-12T00:00:00+00:00',
            'gpa': 3.0
        }


class TestConfig:

    def test_missing_schema(self):
        # No exceptions should occur

        class Doc1(Document):
            pass

        d = Doc1()
        assert isinstance(d.schema, Schema)

    def test_base_config(self):

        class Doc2(Document):
            pass

        assert Doc2.config['collection'] is None
        assert Doc2.config['lazy_collection'] is None
        assert Doc2.config['register_document'] is True

    def test_lazy_collection(self):

        def lazy_factory():
            return "fake_collection"

        class Doc3(Document):
            pass

            class Config:
                lazy_collection = lazy_factory

        assert Doc3.config['collection'] is None
        assert Doc3.config['lazy_collection'] is lazy_factory
        # Try to do the dereferencing
        assert Doc3.collection == "fake_collection"
        d = Doc3()
        assert d.collection == "fake_collection"

    def test_inheritance(self):

        class Doc4(Document):

            class Config:
                collection = "fake_collection"
                register_document = False


        class DocChild4(Doc4):

            class Config:
                collection = "fake_collection_2"

        assert Doc4.config['collection'] == "fake_collection"
        assert Doc4.config['lazy_collection'] is None
        assert Doc4.config['register_document'] is False
        assert DocChild4.config['collection'] == "fake_collection_2"
        assert DocChild4.config['lazy_collection'] is None
        assert DocChild4.config['register_document'] is False
        assert DocChild4.collection == "fake_collection_2"
