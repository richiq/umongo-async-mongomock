from bson import ObjectId
import pytest
from datetime import datetime
from marshmallow import ValidationError

from umongo.data_proxy import DataProxy
from umongo import Document, EmbeddedDocument, Schema, EmbeddedSchema, fields, Reference


class TestFields:

    def test_datetime(self):

        class MySchema(EmbeddedSchema):
            a = fields.DateTimeField()
 
        s = MySchema(strict=True)
        data, _ = s.load({'a': datetime(2016, 8, 6)})
        assert data['a'] == datetime(2016, 8, 6)
        data, _ = s.load({'a': "2016-08-06T00:00:00Z"})
        assert data['a'] == datetime(2016, 8, 6)
        with pytest.raises(ValidationError):
            s.load({'a': "2016-08-06"})
        with pytest.raises(ValidationError):
            s.load({'a': "dummy"})

    def test_dict(self):

        class MySchema(Schema):
            dict = fields.DictField(attribute='in_mongo_dict')

        d = DataProxy(MySchema())
        d.load({'dict': {'a': 1, 'b': {'c': True}}})
        with pytest.raises(KeyError):
            d.get('in_mongo_dict')
        assert d.dump() == {'dict': {'a': 1, 'b': {'c': True}}}
        assert d.get('dict') == {'a': 1, 'b': {'c': True}}
        assert d.to_mongo() == {'in_mongo_dict': {'a': 1, 'b': {'c': True}}}

        # Must manually set_dirty to take the changes into account
        dict_ = d.get('dict')
        dict_['a'] = 1
        assert d.to_mongo(update=True) is None
        dict_.set_modified()
        assert d.to_mongo(update=True) == {'$set': {'in_mongo_dict': {'a': 1, 'b': {'c': True}}}}
        dict_.clear_modified()
        assert d.to_mongo(update=True) is None

        d2 = DataProxy(MySchema(), {'dict': {}})
        d2.to_mongo() == {'dict': {}}

    def test_embedded_document(self):

        class MyEmbeddedDocument(EmbeddedDocument):
            a = fields.IntField(attribute='in_mongo_a')
            b = fields.IntField()

        class MySchema(Schema):
            embedded = fields.EmbeddedField(MyEmbeddedDocument, attribute='in_mongo_embedded')

        # Make sure embedded document doesn't have implicit _id field
        assert '_id' not in MyEmbeddedDocument.Schema().fields
        assert 'id' not in MyEmbeddedDocument.Schema().fields

        d = DataProxy(MySchema())
        d.load(data={'embedded': {'a': 1, 'b': 2}})
        assert d.dump() == {'embedded': {'a': 1, 'b': 2}}
        embedded = d.get('embedded')
        assert type(embedded) == MyEmbeddedDocument
        assert embedded.a == 1
        assert embedded.b == 2
        assert embedded.dump() == {'a': 1, 'b': 2}
        assert embedded.to_mongo() == {'in_mongo_a': 1, 'b': 2}
        assert d.to_mongo() == {'in_mongo_embedded': {'in_mongo_a': 1, 'b': 2}}

        d2 = DataProxy(MySchema())
        d2.from_mongo(data={'in_mongo_embedded': {'in_mongo_a': 1, 'b': 2}})
        assert d == d2

        embedded.a = 3
        assert embedded.to_mongo(update=True) == {'$set': {'in_mongo_a': 3}}
        assert d.to_mongo(update=True) == {'$set': {'in_mongo_embedded': {'in_mongo_a': 3, 'b': 2}}}
        embedded.clear_modified()
        assert embedded.to_mongo(update=True) == None
        assert d.to_mongo(update=True) == None

        del embedded.a
        assert embedded.to_mongo(update=True) == {'$unset': ['in_mongo_a']}
        assert d.to_mongo(update=True) == {'$set': {'in_mongo_embedded': {'b': 2}}}

        d.set('embedded', MyEmbeddedDocument(a=4))
        assert d.get('embedded').to_mongo(update=True) is None
        assert d.to_mongo(update=True) == {'$set': {'in_mongo_embedded': {'in_mongo_a': 4}}}

        embedded_doc = MyEmbeddedDocument(a=1, b=2)
        assert embedded_doc.a == 1
        assert embedded_doc.b == 2
        assert embedded_doc == {'in_mongo_a': 1, 'b': 2}
        assert embedded_doc == MyEmbeddedDocument(a=1, b=2)
        assert embedded_doc['a'] == 1
        assert embedded_doc['b'] == 2

        with pytest.raises(ValidationError):
            MyEmbeddedDocument(in_mongo_a=1, b=2)

        embedded_doc['a'] = 1
        assert embedded_doc.a == embedded_doc['a'] == 1
        del embedded_doc['a']
        assert embedded_doc.a == embedded_doc['a'] == None

        # Test repr readability
        repr_d = repr(MyEmbeddedDocument(a=1, b=2))
        assert 'tests.test_fields.MyEmbeddedDocument' in repr_d
        assert "'in_mongo_a': 1" in repr_d
        assert "'b': 2" in repr_d

    def test_list(self):

        class MySchema(Schema):
            list = fields.ListField(fields.IntField(), attribute='in_mongo_list')

        d = DataProxy(MySchema())
        d.load({'list': [1, 2, 3]})
        assert d.dump() == {'list': [1, 2, 3]}
        assert d.to_mongo() == {'in_mongo_list': [1, 2, 3]}
        assert d.get('list') == [1, 2, 3]
        d.get('list').append(4)
        assert d.to_mongo(update=True) == {'$set': {'in_mongo_list': [1, 2, 3, 4]}}

        d.clear_modified()
        d.set('list', [5, 6, 7])
        assert d.dump() == {'list': [5, 6, 7]}
        assert d.to_mongo(update=True) == {'$set': {'in_mongo_list': [5, 6, 7]}}

        d.clear_modified()
        d.get('list').pop()
        assert d.dump() == {'list': [5, 6]}
        assert d.to_mongo(update=True) == {'$set': {'in_mongo_list': [5, 6]}}

        d.clear_modified()
        d.get('list').clear()
        assert d.dump() == {'list': []}
        assert d.to_mongo(update=True) == {'$unset': ['in_mongo_list']}

        d.set('list', [1, 2, 3])
        d.clear_modified()
        d.get('list').remove(1)
        assert d.dump() == {'list': [2, 3]}
        assert d.to_mongo(update=True) == {'$set': {'in_mongo_list': [2, 3]}}

        d.clear_modified()
        d.get('list').reverse()
        assert d.dump() == {'list': [3, 2]}
        assert d.to_mongo(update=True) == {'$set': {'in_mongo_list': [3, 2]}}

        d.clear_modified()
        d.get('list').sort()
        assert d.dump() == {'list': [2, 3]}
        assert d.to_mongo(update=True) == {'$set': {'in_mongo_list': [2, 3]}}

        d.clear_modified()
        d.get('list').extend([4, 5])
        assert d.dump() == {'list': [2, 3, 4, 5]}
        assert d.to_mongo(update=True) == {'$set': {'in_mongo_list': [2, 3, 4, 5]}}

        # Test repr readability
        repr_d = repr(d.get('list'))
        assert repr_d == "<object umongo.data_objects.List([2, 3, 4, 5])>"

    def test_objectid(self):

        class MySchema(Schema):
            objid = fields.ObjectIdField(attribute='in_mongo_objid')

        d = DataProxy(MySchema())
        d.load({'objid': ObjectId("5672d47b1d41c88dcd37ef05")})
        assert d.dump() == {'objid': "5672d47b1d41c88dcd37ef05"}
        assert d.to_mongo() == {'in_mongo_objid': ObjectId("5672d47b1d41c88dcd37ef05")}
        d.load({'objid': "5672d47b1d41c88dcd37ef05"})
        assert d.dump() == {'objid': "5672d47b1d41c88dcd37ef05"}
        assert d.to_mongo() == {'in_mongo_objid': ObjectId("5672d47b1d41c88dcd37ef05")}
        assert d.get('objid') == ObjectId("5672d47b1d41c88dcd37ef05")

        d.set('objid', ObjectId("5672d5e71d41c88f914b77c4"))
        d.to_mongo(update=True) == {
            '$set': {'in_mongo_objid': ObjectId("5672d5e71d41c88f914b77c4")}}

        d.set('objid', ObjectId("5672d5e71d41c88f914b77c4"))
        d.to_mongo(update=True) == {
            '$set': {'in_mongo_objid': ObjectId("5672d5e71d41c88f914b77c4")}}

        d.set('objid', "5672d5e71d41c88f914b77c4")
        assert d.get('objid') == ObjectId("5672d5e71d41c88f914b77c4")

        with pytest.raises(ValidationError):
            d.set('objid', 'notanid')

    def test_reference(self):

        class MyReferencedDoc(Document):
            pass

        class OtherDoc(Document):
            pass

        to_refer_doc = MyReferencedDoc.build_from_mongo(
            {'_id': ObjectId("5672d47b1d41c88dcd37ef05")})

        other_doc = OtherDoc.build_from_mongo(
            {'_id': ObjectId("5672d47b1d41c88dcd37ef07")})

        class MySchema(Schema):
            ref = fields.ReferenceField(MyReferencedDoc, attribute='in_mongo_ref')

        d = DataProxy(MySchema())
        d.load({'ref': ObjectId("5672d47b1d41c88dcd37ef05")})
        d.load({'ref': "5672d47b1d41c88dcd37ef05"})
        assert d.dump() == {'ref': "5672d47b1d41c88dcd37ef05"}
        d.get('ref').document_cls == MyReferencedDoc
        d.set('ref', to_refer_doc)
        assert d.to_mongo(update=True) == {'$set': {'in_mongo_ref': to_refer_doc.pk}}
        assert d.get('ref').document_cls == MyReferencedDoc
        good_ref = Reference(MyReferencedDoc, to_refer_doc.pk)
        d.set('ref', good_ref)
        assert d.get('ref') == good_ref

        with pytest.raises(ValidationError):
            d.set('ref', other_doc)
        not_created_doc = MyReferencedDoc()
        with pytest.raises(ValidationError):
            d.set('ref', not_created_doc)
        bad_ref = Reference(OtherDoc, other_doc.pk)
        with pytest.raises(ValidationError):
            d.set('ref', bad_ref)

    def test_reference_lazy(self):

        class MyReferencedDocLazy(Document):
            pass

        to_refer_doc = MyReferencedDocLazy.build_from_mongo(
            {'_id': ObjectId("5672d47b1d41c88dcd37ef05")})

        class MySchema(Schema):
            ref = fields.ReferenceField("MyReferencedDocLazy", attribute='in_mongo_ref')

        d = DataProxy(MySchema())
        d.load({'ref': ObjectId("5672d47b1d41c88dcd37ef05")})
        d.load({'ref': "5672d47b1d41c88dcd37ef05"})
        assert d.dump() == {'ref': "5672d47b1d41c88dcd37ef05"}
        assert d.get('ref').document_cls == MyReferencedDocLazy
        d.set('ref', to_refer_doc)
        assert d.to_mongo(update=True) == {'$set': {'in_mongo_ref': to_refer_doc.pk}}
        assert d.get('ref').document_cls == MyReferencedDocLazy
