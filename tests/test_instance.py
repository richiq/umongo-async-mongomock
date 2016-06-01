import pytest
from bson import ObjectId

from umongo import (Document, fields, AlreadyRegisteredDocumentError, EmbeddedDocument,
                    NotRegisteredDocumentError, NoDBDefinedError)
from umongo.instance import Instance, LazyLoaderInstance
from umongo.document import DocumentTemplate, DocumentImplementation
from umongo.embedded_document import EmbeddedDocumentTemplate, EmbeddedDocumentImplementation

from .common import MokedDB, MokedBuilder
from .fixtures import instance


@pytest.fixture
def db():
    return MokedDB('my_db')


class TestInstance:

    def test_already_register(self, instance):

        class Doc(Document):
            pass

        implementation = instance.register(Doc)
        assert issubclass(implementation, DocumentImplementation)
        with pytest.raises(AlreadyRegisteredDocumentError):
            instance.register(Doc)

        class Embedded(EmbeddedDocument):
            pass

        implementation = instance.register(Embedded)
        assert issubclass(implementation, EmbeddedDocumentImplementation)
        with pytest.raises(AlreadyRegisteredDocumentError):
            instance.register(Embedded)

    def test_not_register_documents(self, instance):

        with pytest.raises(NotRegisteredDocumentError):
            @instance.register
            class Doc1(Document):
                ref = fields.ReferenceField('DummyDoc')
            Doc1(ref=ObjectId('56dee8dd1d41c8860b263d86'))

        with pytest.raises(NotRegisteredDocumentError):
            @instance.register
            class Doc2(Document):
                nested = fields.EmbeddedField('DummyNested')
            Doc2(nested={})

    def test_multiple_instances(self, db):
        instance1 = Instance(db)
        instance2 = Instance(db)

        class Doc(Document):
            pass

        class Embedded(EmbeddedDocument):
            pass

        Doc1 = instance1.register(Doc)
        Doc2 = instance2.register(Doc)
        Embedded1 = instance1.register(Embedded)
        Embedded2 = instance2.register(Embedded)

        assert issubclass(Doc1, DocumentImplementation)
        assert issubclass(Doc2, DocumentImplementation)
        assert issubclass(Embedded1, EmbeddedDocumentImplementation)
        assert issubclass(Embedded2, EmbeddedDocumentImplementation)
        assert Doc1.opts.instance is instance1
        assert Doc2.opts.instance is instance2
        assert Embedded1.opts.instance is instance1
        assert Embedded2.opts.instance is instance2

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

        class Embedded(EmbeddedDocument):
            pass

        embedded_instance1_cls = instance1.register(Embedded)
        embedded_instance2_cls = instance2.register(embedded_instance1_cls)
        assert issubclass(embedded_instance2_cls, EmbeddedDocumentImplementation)
        with pytest.raises(AlreadyRegisteredDocumentError):
            instance2.register(Embedded)

    def test_parent_not_registered(self, instance):
        class Parent(Document):
            pass

        with pytest.raises(NotRegisteredDocumentError):
            @instance.register
            class Child(Parent):
                pass

        class ParentEmbedded(EmbeddedDocument):
            pass

        with pytest.raises(NotRegisteredDocumentError):
            @instance.register
            class ChildEmbedded(ParentEmbedded):
                pass

    def test_retrieve_registered(self, instance):
        class Doc(Document):
            pass

        class Embedded(EmbeddedDocument):
            pass

        Doc_imp = instance.register(Doc)
        Embedded_imp = instance.register(Embedded)

        assert instance.retrieve_document('Doc') is Doc_imp
        assert instance.retrieve_document(Doc) is Doc_imp
        assert instance.retrieve_embedded_document('Embedded') is Embedded_imp
        assert instance.retrieve_embedded_document(Embedded) is Embedded_imp

        with pytest.raises(NotRegisteredDocumentError):
            instance.retrieve_document('Dummy')

        with pytest.raises(NotRegisteredDocumentError):
            instance.retrieve_embedded_document('Dummy')

    def test_mix_doc_and_embedded(self, instance):
        @instance.register
        class Doc(Document):
            pass

        @instance.register
        class Embedded(EmbeddedDocument):
            pass

        with pytest.raises(NotRegisteredDocumentError):
            instance.retrieve_document('Embedded')

        with pytest.raises(NotRegisteredDocumentError):
            instance.retrieve_embedded_document('Doc')

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

    def test_patched_fields(self, db):

        instance1 = Instance(db)
        instance2 = Instance(db)

        class Embedded(EmbeddedDocument):
            simple = fields.IntField()

        Embedded1 = instance1.register(Embedded)
        Embedded2 = instance2.register(Embedded1)

        class ToRef(Document):
            pass

        ToRef1 = instance1.register(ToRef)
        ToRef2 = instance2.register(ToRef)

        class Doc(Document):
            embedded = fields.EmbeddedField(Embedded1)
            ref = fields.ReferenceField(ToRef1)

        Doc1 = instance1.register(Doc)
        Doc2 = instance2.register(Doc)

        assert issubclass(Doc.embedded.embedded_document, EmbeddedDocumentTemplate)
        assert issubclass(Doc1.schema.fields['embedded'].embedded_document, EmbeddedDocumentTemplate)
        assert issubclass(Doc2.schema.fields['embedded'].embedded_document, EmbeddedDocumentTemplate)
        assert issubclass(Doc1.schema.fields['embedded'].embedded_document_cls, EmbeddedDocumentImplementation)
        assert issubclass(Doc2.schema.fields['embedded'].embedded_document_cls, EmbeddedDocumentImplementation)

        assert issubclass(Doc.ref.document, DocumentTemplate)
        assert issubclass(Doc1.schema.fields['ref'].document, DocumentTemplate)
        assert issubclass(Doc2.schema.fields['ref'].document, DocumentTemplate)
        assert issubclass(Doc1.schema.fields['ref'].document_cls, DocumentImplementation)
        assert issubclass(Doc2.schema.fields['ref'].document_cls, DocumentImplementation)

        assert Embedded1.schema.fields['simple'].instance is instance1
        assert Embedded1.opts.instance is instance1
        assert Embedded2.schema.fields['simple'].instance is instance2
        assert Embedded2.opts.instance is instance2

        assert Doc1.schema.fields['embedded'].instance is instance1
        assert Doc1.opts.instance is instance1
        assert Doc2.schema.fields['embedded'].instance is instance2
        assert Doc2.opts.instance is instance2
