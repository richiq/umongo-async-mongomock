import pytest
from datetime import datetime
from bson import ObjectId, DBRef
from functools import namedtuple

# from .fixtures import collection_moke, dal_moke, moked_lazy_loader

from umongo import Document, Schema, fields, exceptions
from umongo.abstract import AbstractDal

from .common import BaseTest


class BaseStudent(Document):
    name = fields.StrField(required=True)
    birthday = fields.DateTimeField()
    gpa = fields.FloatField()

    class Meta:
        abstract = True


class Student(BaseStudent):
    pass


class EasyIdStudent(BaseStudent):
    id = fields.IntField(attribute='_id')

    class Meta:
        collection_name = 'student'


class TestDocument(BaseTest):

    def setup(self):
        super().setup()
        self.instance.register(BaseStudent)
        self.Student = self.instance.register(Student)
        self.EasyIdStudent = self.instance.register(EasyIdStudent)

    def test_repr(self):
        # I love readable stuff !
        john = self.Student(name='John Doe', birthday=datetime(1995, 12, 12), gpa=3.0)
        assert 'tests.test_document.Student' in repr(john)
        assert 'name' in repr(john)
        assert 'birthday' in repr(john)
        assert 'gpa' in repr(john)

    def test_create(self):
        john = self.Student(name='John Doe', birthday=datetime(1995, 12, 12), gpa=3.0)
        assert john.to_mongo() == {
            'name': 'John Doe',
            'birthday': datetime(1995, 12, 12),
            'gpa': 3.0
        }
        assert john.created is False
        with pytest.raises(exceptions.NotCreatedError):
            john.to_mongo(update=True)

    def test_from_mongo(self):
        john = self.Student.build_from_mongo(data={
            'name': 'John Doe', 'birthday': datetime(1995, 12, 12), 'gpa': 3.0})
        assert john.to_mongo(update=True) is None
        assert john.created is True
        assert john.to_mongo() == {
            'name': 'John Doe',
            'birthday': datetime(1995, 12, 12),
            'gpa': 3.0
        }

    def test_update(self):
        john = self.Student.build_from_mongo(data={
            'name': 'John Doe', 'birthday': datetime(1995, 12, 12), 'gpa': 3.0})
        john.name = 'William Doe'
        john.birthday = datetime(1996, 12, 12)
        assert john.to_mongo(update=True) == {
            '$set': {'name': 'William Doe', 'birthday': datetime(1996, 12, 12)}}
        john.clear_modified()
        assert john.to_mongo(update=True) is None

    def test_dump(self):
        john = self.Student.build_from_mongo(data={
            'name': 'John Doe', 'birthday': datetime(1995, 12, 12), 'gpa': 3.0})
        assert john.dump() == {
            'name': 'John Doe',
            'birthday': '1995-12-12T00:00:00+00:00',
            'gpa': 3.0
        }

    def test_fields_by_attr(self):
        john = self.Student.build_from_mongo(data={
            'name': 'John Doe', 'birthday': datetime(1995, 12, 12), 'gpa': 3.0})
        assert john.name == 'John Doe'
        john.name = 'William Doe'
        assert john.name == 'William Doe'
        del john.name
        assert john.name is None
        with pytest.raises(AttributeError):
            john.missing
        with pytest.raises(AttributeError):
            john.missing = None
        with pytest.raises(AttributeError):
            del john.missing
        with pytest.raises(AttributeError):
            del john.commit

    def test_fields_by_items(self):
        john = self.Student.build_from_mongo(data={
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
        john = self.Student.build_from_mongo(data={
            'name': 'John Doe', 'birthday': datetime(1995, 12, 12), 'gpa': 3.0})
        assert john.pk is None
        john_id = ObjectId("5672d47b1d41c88dcd37ef05")
        john = self.Student.build_from_mongo(data={
            '_id': john_id, 'name': 'John Doe',
            'birthday': datetime(1995, 12, 12), 'gpa': 3.0})
        assert john.pk == john_id

        # Don't do that in real life !
        @self.instance.register
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

    def test_dbref(self):
        student = self.Student()
        with pytest.raises(exceptions.NotCreatedError):
            student.dbref
        # Fake document creation
        student.id = ObjectId('573b352e13adf20d13d01523')
        student.created = True
        student.clear_modified()
        assert student.dbref == DBRef(collection='student',
                                      id=ObjectId('573b352e13adf20d13d01523'))

    def test_equality(self):
        john_data = {
            '_id': 42, 'name': 'John Doe', 'birthday': datetime(1995, 12, 12), 'gpa': 3.0
        }
        john = self.EasyIdStudent.build_from_mongo(data=john_data)
        john2 = self.EasyIdStudent.build_from_mongo(data=john_data)
        phillipe = self.EasyIdStudent.build_from_mongo(data={
            '_id': 3, 'name': 'Phillipe J. Fry', 'birthday': datetime(1995, 12, 12), 'gpa': 3.0})

        assert john != phillipe
        assert john2 == john
        assert john == DBRef(collection='student', id=john.pk)

        john.name = 'William Doe'
        assert john == john2

        newbie = self.EasyIdStudent(name='Newbie')
        newbie2 = self.EasyIdStudent(name='Newbie')
        assert newbie != newbie2

    @pytest.mark.xfail
    def test_dal_connection(self, collection_moke):
        # TODO check this...

        @self.instance.register
        class ConfiguredStudent(Student):
            id = fields.IntField(attribute='_id')

            class Meta:
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
        # Should be able to instanciate document without their required fields
        student = self.Student()
        student = self.Student(gpa=2.8)
        # Required check is done in `io_validate`, cannot go further without a dal
        # TODO check this...

    def test_auto_id_field(self):
        my_id = ObjectId('5672d47b1d41c88dcd37ef05')

        @self.instance.register
        class AutoId(Document):

            class Meta:
                allow_inheritance = True

        assert 'id' in AutoId.schema.fields

        # default id field is only dumpable
        with pytest.raises(exceptions.ValidationError):
            AutoId(id=my_id)

        autoid = AutoId.build_from_mongo({'_id': my_id})
        assert autoid.id == my_id
        assert autoid.pk == autoid.id
        assert autoid.dump() == {'id': '5672d47b1d41c88dcd37ef05'}

        @self.instance.register
        class AutoIdInheritance(AutoId):
            pass

        assert 'id' in AutoIdInheritance.schema.fields

    def test_custom_id_field(self):
        my_id = ObjectId('5672d47b1d41c88dcd37ef05')

        @self.instance.register
        class CustomId(Document):
            int_id = fields.IntField(attribute='_id')

            class Meta:
                allow_inheritance = True

        assert 'id' not in CustomId.schema.fields
        with pytest.raises(exceptions.ValidationError):
            CustomId(id=my_id)
        customid = CustomId(int_id=42)
        with pytest.raises(exceptions.ValidationError):
            customid.int_id = my_id
        assert customid.int_id == 42
        assert customid.pk == customid.int_id
        assert customid.to_mongo() == {'_id': 42}

        @self.instance.register
        class CustomIdInheritance(CustomId):
            pass

        assert 'id' not in CustomIdInheritance.schema.fields

    def test_inheritance_from_template(self):
        # It is legal (and equivalent) to make a child inherit from
        # a template instead of from an implementation

        class ParentAsTemplate(Document):
            class Meta:
                allow_inheritance = True

        Parent = self.instance.register(ParentAsTemplate)

        assert Parent.template is ParentAsTemplate

        @self.instance.register
        class Child(ParentAsTemplate):
            pass

        assert Parent.opts.children == {'Child'}


class TestConfig(BaseTest):

    def test_missing_schema(self):
        # No exceptions should occur

        @self.instance.register
        class Doc(Document):
            pass

        d = Doc()
        assert isinstance(d.schema, Schema)

    def test_base_config(self):

        @self.instance.register
        class Doc(Document):
            pass

        assert Doc.opts.collection_name == 'doc'
        assert Doc.opts.abstract is False
        assert Doc.opts.allow_inheritance is False
        assert Doc.opts.instance is self.instance
        assert Doc.opts.is_child is False
        assert Doc.opts.indexes == []
        assert Doc.opts.children == set()

    @pytest.mark.xfail
    def test_lazy_collection(self, moked_lazy_loader, collection_moke):

        def lazy_factory():
            return collection_moke

        class Doc3(Document):

            class Meta:
                lazy_collection = moked_lazy_loader(lazy_factory)

        assert Doc3.opts.collection is None
        assert Doc3.opts.dal is Doc3.Meta.lazy_collection.dal
        assert issubclass(Doc3, Doc3.Meta.lazy_collection.dal)
        # Try to do the dereferencing
        assert Doc3.collection is collection_moke
        d = Doc3()
        assert d.collection is collection_moke

    @pytest.mark.xfail
    def test_custom_dal_lazy_collection(self, request, moked_lazy_loader, collection_moke):

        dal_moke_2 = dal_moke(request, collection_moke)

        def lazy_factory():
            return collection_moke

        class Doc3(Document):

            class Meta:
                lazy_collection = moked_lazy_loader(lazy_factory)
                dal = dal_moke_2
                register_document = False

        assert Doc3.opts.dal is dal_moke_2
        assert issubclass(Doc3, dal_moke_2)

    def test_inheritance(self):

        @self.instance.register
        class AbsDoc(Document):

            class Meta:
                abstract = True

        @self.instance.register
        class DocChild1(AbsDoc):

            class Meta:
                allow_inheritance = True
                collection_name = 'col1'

        @self.instance.register
        class DocChild1Child(DocChild1):
            pass

        @self.instance.register
        class DocChild2(AbsDoc):

            class Meta:
                collection_name = 'col2'

        assert DocChild1.opts.collection_name is 'col1'
        assert DocChild1Child.opts.collection_name is 'col1'
        assert DocChild1Child.opts.allow_inheritance is False
        assert DocChild2.opts.collection_name == 'col2'

    def test_bad_inheritance(self):
        with pytest.raises(exceptions.DocumentDefinitionError) as exc:
            @self.instance.register
            class BadAbstractDoc(Document):
                class Meta:
                    allow_inheritance = False
                    abstract = True
        assert exc.value.args[0] == "Abstract document cannot disable inheritance"

        @self.instance.register
        class NotParent(Document):
            pass

        assert not NotParent.opts.allow_inheritance

        with pytest.raises(exceptions.DocumentDefinitionError) as exc:
            @self.instance.register
            class ImpossibleChildDoc(NotParent):
                pass
        assert exc.value.args[0] == ("Document"
            " <class 'tests.test_document.NotParent'>"
            " doesn't allow inheritance")

        @self.instance.register
        class NotAbstractParent(Document):
            class Meta:
                allow_inheritance = True

        with pytest.raises(exceptions.DocumentDefinitionError) as exc:
            @self.instance.register
            class ImpossibleChildDoc(NotAbstractParent):
                class Meta:
                    abstract = True
        assert exc.value.args[0] == "Abstract document should have all it parents abstract"

        @self.instance.register
        class ParentWithCol1(Document):
            class Meta:
                allow_inheritance = True
                collection_name = 'col1'

        @self.instance.register
        class ParentWithCol2(Document):
            class Meta:
                allow_inheritance = True
                collection_name = 'col2'

        with pytest.raises(exceptions.DocumentDefinitionError) as exc:
            @self.instance.register
            class ImpossibleChildDoc(ParentWithCol1):
                class Meta:
                    collection_name = 'col42'
        assert exc.value.args[0].startswith("Cannot redefine collection_name in a child, use abstract instead")

        with pytest.raises(exceptions.DocumentDefinitionError) as exc:
            @self.instance.register
            class ImpossibleChildDoc(ParentWithCol1, ParentWithCol2):
                pass
        assert exc.value.args[0].startswith("Cannot redefine collection_name in a child, use abstract instead")

    @pytest.mark.xfail
    def test_bad_lazy_collection(self, dal_moke):

        # Bad `dal` attribute
        with pytest.raises(exceptions.NoCollectionDefinedError) as exc:

            class Doc7(Document):

                class Meta:
                    lazy_collection = lambda: None

                    class dal:
                        pass
        assert exc.value.args[0] == (
            "`dal` attribute must be a subclass of <class 'umongo.abstract.AbstractDal'>")

        # Invalid lazy_collection's dal
        LazyCollection = namedtuple('LazyCollection', ('dal', 'load'))

        class BadDal:
            pass

        def load_collection():
            pass

        with pytest.raises(exceptions.NoCollectionDefinedError) as exc:
            class Doc8(Document):
                class Meta:
                    lazy_collection = LazyCollection(BadDal, load_collection)
        assert exc.value.args[0] == (
            "`dal` attribute must be a subclass of <class 'umongo.abstract.AbstractDal'>")

        # Invalid lazy_collection's load
        class GoodDal(AbstractDal):
            @staticmethod
            def io_validate_patch_schema(schema):
                pass

        class Doc9(Document):
            class Meta:
                lazy_collection = LazyCollection(GoodDal, load_collection)

        with pytest.raises(exceptions.NoCollectionDefinedError) as exc:
            Doc9.collection
        assert exc.value.args[0] == "lazy_collection didn't returned a collection"
