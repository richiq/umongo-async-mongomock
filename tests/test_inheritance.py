import pytest

from umongo import Document, fields, exceptions

from .fixtures import collection_moke, dal_moke


class TestInheritance:

    def test_cls_field(self):

        class Parent1(Document):
            last_name = fields.StrField()

            class Meta:
                allow_inheritance = True

        class Child1(Parent1):
            first_name = fields.StrField()

        assert '_cls' in Child1.schema.fields
        cls_field = Child1.schema.fields['_cls']
        assert not hasattr(Parent1(), '_cls')
        assert Child1()._cls == 'Child1'

    def test_simple(self, collection_moke, dal_moke):

        class Parent2(Document):
            last_name = fields.StrField()

            class Meta:
                allow_inheritance = True
                collection = collection_moke

        assert Parent2.opts.abstract == False
        assert Parent2.opts.allow_inheritance == True

        class Child2(Parent2):
            first_name = fields.StrField()

        assert Child2.opts.abstract == False
        assert Child2.opts.allow_inheritance == False
        assert Child2.collection == collection_moke
        child = Child2(first_name='John', last_name='Doe')

    def test_abstract(self, collection_moke, dal_moke):

        # Cannot define a collection for an abstract doc !
        with pytest.raises(exceptions.DocumentDefinitionError):
            class BadAbstractDoc(Document):
                class Meta:
                    abstract = True
                    collection = collection_moke

        class AbstractDoc(Document):
            abs_field = fields.StrField(missing='from abstract')
            class Meta:
                abstract = True

        assert AbstractDoc.opts.abstract == True
        assert AbstractDoc.opts.allow_inheritance == True
        # Cannot instanciate also
        with pytest.raises(exceptions.AbstractDocumentError):
            AbstractDoc()

        class StillAbstractDoc(AbstractDoc):
            class Meta:
                abstract = True
        assert StillAbstractDoc.opts.abstract == True
        assert StillAbstractDoc.opts.allow_inheritance == True

        class ConcreteDoc(AbstractDoc):
            pass
        assert ConcreteDoc.opts.abstract == False
        assert ConcreteDoc.opts.allow_inheritance == False
        assert ConcreteDoc().abs_field == 'from abstract'
