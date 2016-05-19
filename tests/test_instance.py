import pytest
from bson import ObjectId

from umongo import (Document, fields, AlreadyRegisteredDocumentError,
                    NotRegisteredDocumentError, NoDBDefinedError)
from umongo.instance import Instance, LazyLoaderInstance
from umongo.document import DocumentImplementation

from .common import MokedDB, MokedBuilder
from .fixtures import instance


@pytest.fixture
def db():
    return MokedDB('my_db')


class TestInstance:

    def test_already_register_documents(self, instance):

        class Doc(Document):
            pass

        doc_instance = instance.register(Doc)
        assert issubclass(doc_instance, DocumentImplementation)
        with pytest.raises(AlreadyRegisteredDocumentError):
            instance.register(Doc)

    def test_not_register_documents(self, instance):

        @instance.register
        class Doc(Document):
            ref = fields.ReferenceField('DummyDoc')

        with pytest.raises(NotRegisteredDocumentError):
            Doc(ref=ObjectId('56dee8dd1d41c8860b263d86'))

    def test_multiple_instances(self, db):
        instance1 = Instance(db)
        instance2 = Instance(db)

        class Doc(Document):
            pass

        instance1.register(Doc)
        instance2.register(Doc)

    def test_register_other_implementation(self, db):
        instance1 = Instance(db)
        instance2 = Instance(db)

        class Doc(Document):
            pass

        doc_instance1_cls = instance1.register(Doc)
        doc_instance2_cls = instance2.register(doc_instance1_cls)
        assert issubclass(doc_instance2_cls, DocumentImplementation)
        with pytest.raises(AlreadyRegisteredDocumentError):
            instance2.register(Doc)

    def test_parent_not_registered(self, instance):
        class Parent(Document):
            pass

        with pytest.raises(NotRegisteredDocumentError):
            @instance.register
            class Child(Parent):
                pass

    def test_lazy_loader_instance(self, db):

        class MokedInstance(LazyLoaderInstance):
            BUILDER_CLS = MokedBuilder

        instance = MokedInstance()

        class Doc(Document):
            pass

        doc_impl_cls = instance.register(Doc)

        with pytest.raises(NoDBDefinedError):
            doc_impl_cls.collection

        instance.init(db)

        assert doc_impl_cls.collection == db['doc']
