import pytest
from datetime import datetime
from bson import ObjectId

from .common import BaseTest
from umongo import Document, Schema, fields, exceptions


class Student(Document):

    class Schema(Schema):
        name = fields.StrField(required=True)
        birthday = fields.DateTimeField()
        gpa = fields.FloatField()


class TestDocument(BaseTest):

    def test_repr(self):
        # I love readable stuff !
        john = Student(name='John Doe', birthday=datetime(1995, 12, 12), gpa=3.0)
        assert 'tests.test_document.Student' in repr(john)
        assert 'name' in repr(john)
        assert 'birthday' in repr(john)
        assert 'gpa' in repr(john)

    def test_create(self):
        john = Student(name='John Doe', birthday=datetime(1995, 12, 12), gpa=3.0)
        assert john.to_mongo() == {
            'name': 'John Doe',
            'birthday': datetime(1995, 12, 12),
            'gpa': 3.0
        }
        assert john.created is False
        with pytest.raises(exceptions.NotCreatedError):
            john.to_mongo(update=True)

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
        john.name = 'William Doe'
        john.birthday = datetime(1996, 12, 12)
        assert john.to_mongo(update=True) == {
            '$set': {'name': 'William Doe', 'birthday': datetime(1996, 12, 12)}}
        john.clear_modified()
        assert john.to_mongo(update=True) is None

    def test_dump(self):
        john = Student.build_from_mongo(data={
            'name': 'John Doe', 'birthday': datetime(1995, 12, 12), 'gpa': 3.0})
        assert john.dump() == {
            'name': 'John Doe',
            'birthday': '1995-12-12T00:00:00+00:00',
            'gpa': 3.0
        }

    def test_fields_by_attr(self):
        john = Student.build_from_mongo(data={
            'name': 'John Doe', 'birthday': datetime(1995, 12, 12), 'gpa': 3.0})
        assert john.name == 'John Doe'
        john.name = 'William Doe'
        assert john.name == 'William Doe'
        del john.name
        assert john.name is None
        with pytest.raises(KeyError):
            john.missing
        with pytest.raises(KeyError):
            john.missing = None
        with pytest.raises(KeyError):
            del john.missing
        with pytest.raises(KeyError):
            del john.commit

    def test_fields_by_items(self):
        john = Student.build_from_mongo(data={
            'name': 'John Doe', 'birthday': datetime(1995, 12, 12), 'gpa': 3.0})
        assert john['name'] == 'John Doe'
        john['name'] = 'William Doe'
        assert john['name'] == 'William Doe'
        del john['name']
        assert john['name'] is None
        with pytest.raises(KeyError):
            john['missing']
        with pytest.raises(KeyError):
            john['missing'] = None
        with pytest.raises(KeyError):
            del john['missing']

    def test_pk(self):
        john = Student.build_from_mongo(data={
            'name': 'John Doe', 'birthday': datetime(1995, 12, 12), 'gpa': 3.0})
        assert john.pk is None
        john_id = ObjectId("5672d47b1d41c88dcd37ef05")
        john = Student.build_from_mongo(data={
            '_id': john_id, 'name': 'John Doe',
            'birthday': datetime(1995, 12, 12), 'gpa': 3.0})
        assert john.pk == john_id

        # Don't do that in real life !
        class CrazyNaming(Document):
            id = fields.IntField(attribute='in_mongo_id')
            _id = fields.IntField(attribute='in_mongo__id')
            pk = fields.IntField()
            real_pk = fields.IntField(attribute='_id')

        crazy = CrazyNaming.build_from_mongo(data={
            '_id': 1, 'in_mongo__id': 2, 'in_mongo__id': 3, 'pk': 4
            })
        assert crazy.pk == crazy.real_pk == 1
        assert crazy['pk'] == 4


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

    def test_no_collection(self):

        class Doc5(Document):
            pass

        with pytest.raises(exceptions.NoCollectionDefinedError):
            Doc5.collection

        with pytest.raises(exceptions.NoCollectionDefinedError):
            Doc5().collection

    def test_bad_lazy_collection(self):

        class Doc6(Document):

            class Config:
                lazy_collection = lambda: None

        with pytest.raises(exceptions.NoCollectionDefinedError):
            Doc6.collection

        with pytest.raises(exceptions.NoCollectionDefinedError):
            Doc6().collection
