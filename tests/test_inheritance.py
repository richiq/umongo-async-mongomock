import pytest

from umongo import Document, fields, exceptions

from .fixtures import db_moke, dal_moke


class TestInheritance:

    def test_cls_field(self):

        class Parent1(Document):
            last_name = fields.StrField()

            class Meta:
                allow_inheritance = True

        class Child1(Parent1):
            first_name = fields.StrField()

        assert 'cls' in Child1.schema.fields
        cls_field = Child1.schema.fields['cls']
        assert not hasattr(Parent1(), 'cls')
        assert Child1().cls == 'Child1'

        loaded = Parent1.build_from_mongo(
            {'_cls': 'Child1', 'first_name': 'John', 'last_name': 'Doe'}, use_cls=True)
        assert loaded.cls == 'Child1'

    def test_simple(self, db_moke, dal_moke):

        class Parent2(Document):
            last_name = fields.StrField()

            class Meta:
                allow_inheritance = True
                db = db_moke

        assert Parent2.opts.abstract == False
        assert Parent2.opts.allow_inheritance == True

        class Child2(Parent2):
            first_name = fields.StrField()

        assert Child2.opts.abstract == False
        assert Child2.opts.allow_inheritance == False
        assert Child2.db is db_moke
        assert Child2.collection is Parent2.collection
        child = Child2(first_name='John', last_name='Doe')

    def test_abstract(self, db_moke, dal_moke):

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
