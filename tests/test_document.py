import pytest
from datetime import datetime
from bson import ObjectId, DBRef

from .common import BaseTest
from .fixtures import collection_moke, dal_moke

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

    def test_dbref(self, collection_moke):

        class ConfiguredStudent(Student):
            id = fields.IntField(attribute='_id')

            class Config:
                collection = collection_moke

        student = ConfiguredStudent()

        with pytest.raises(exceptions.NotCreatedError):
            student.dbref

        # Fake document creation
        student.id = 1
        student.created = True
        student.clear_modified()

        assert student.dbref == DBRef(collection=collection_moke.name, id=1)

    def test_equality(self, collection_moke):

        class ConfiguredStudent(Student):
            id = fields.IntField(attribute='_id')

            class Config:
                collection = collection_moke

        john_data = {
            '_id': 42, 'name': 'John Doe', 'birthday': datetime(1995, 12, 12), 'gpa': 3.0
        }
        john = ConfiguredStudent.build_from_mongo(data=john_data)
        john2 = ConfiguredStudent.build_from_mongo(data=john_data)
        phillipe = ConfiguredStudent.build_from_mongo(data={
            '_id': 3, 'name': 'Phillipe J. Fry', 'birthday': datetime(1995, 12, 12), 'gpa': 3.0})

        assert john != phillipe
        assert john2 == john
        assert john == DBRef(collection=collection_moke.name, id=john.pk)

        john.name = 'William Doe'
        assert john == john2

        newbie = ConfiguredStudent(name='Newbie')
        newbie2 = ConfiguredStudent(name='Newbie')
        assert newbie != newbie2

    def test_dal_connection(self, collection_moke):

        class ConfiguredStudent(Student):
            id = fields.IntField(attribute='_id')

            class Config:
                collection = collection_moke

        newbie = ConfiguredStudent(name='Newbie')

        def commiter(doc, io_validate_all=False):
            doc.created = True

        collection_moke.push_callback('commit', callback=commiter)
        collection_moke.push_callback('reload')
        collection_moke.push_callback('delete')
        collection_moke.push_callback('find_one')
        collection_moke.push_callback('find')
        collection_moke.push_callback('io_validate')

        with collection_moke:
            newbie.commit()
            newbie.reload()
            newbie.delete()
            newbie.find_one()
            newbie.find()
            newbie.io_validate()

    def test_required_fields(self):

        # Should be able to instanciate document without there required field
        student = Student()
        student = Student(gpa=2.8)
        # Required check is done in `io_validate`, cannot go further without a dal


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
        assert Doc2.config['dal'] is None
        assert Doc2.config['register_document'] is True

    def test_lazy_collection(self, dal_moke, collection_moke):

        def lazy_factory():
            return collection_moke

        class Doc3(Document):

            class Config:
                lazy_collection = lazy_factory
                dal = dal_moke

        assert Doc3.config['collection'] is None
        assert Doc3.config['lazy_collection'] is lazy_factory
        assert Doc3.config['dal'] is dal_moke
        assert issubclass(Doc3, dal_moke)
        # Try to do the dereferencing
        assert Doc3.collection is collection_moke
        d = Doc3()
        assert d.collection is collection_moke

    def test_inheritance(self, request):
        col1 = collection_moke(request, name='col1')
        col2 = collection_moke(request, name='col2')

        class Doc4(Document):

            class Config:
                collection = col1
                register_document = False


        class DocChild4(Doc4):

            class Config:
                collection = col2

        assert Doc4.config['collection'] is col1
        assert Doc4.config['register_document'] is False
        assert DocChild4.config['collection'] == col2
        assert DocChild4.config['register_document'] is False
        assert DocChild4.collection is col2

    def test_no_collection(self):

        class Doc5(Document):
            pass

        with pytest.raises(exceptions.NoCollectionDefinedError):
            Doc5.collection

        with pytest.raises(exceptions.NoCollectionDefinedError):
            Doc5().collection

    def test_bad_lazy_collection(self, dal_moke):

        # Missing `dal` attribute
        with pytest.raises(exceptions.NoCollectionDefinedError):

            class Doc7(Document):

                class Config:
                    lazy_collection = lambda: None

        # Bad `dal` attribute
        with pytest.raises(exceptions.NoCollectionDefinedError):

            class Doc7(Document):

                class Config:
                    lazy_collection = lambda: None

                    class dal:
                        pass
