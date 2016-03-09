from bson import ObjectId
import pytest
from datetime import datetime
from marshmallow import ValidationError

from umongo.data_proxy import DataProxy
from umongo import Document, EmbeddedDocument, Schema, NestedSchema, fields


class TestFields:

    def test_datetime(self):

        class MySchema(NestedSchema):
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

    def test_nested(self):

        class MyNestedSchema(NestedSchema):
            a = fields.IntField(attribute='in_mongo_a')
            b = fields.IntField()

        class MySchema(Schema):
            nested = fields.NestedField(MyNestedSchema(), attribute='in_mongo_nested')

        d = DataProxy(MySchema())
        d.load({'nested': {'a': 1, 'b': 2}})
        with pytest.raises(KeyError):
            d.in_mongo_nested
        assert d.dump() == {'nested': {'a': 1, 'b': 2}}
        assert d.nested == {'in_mongo_a': 1, 'b': 2}
        assert d.to_mongo() == {'in_mongo_nested': {'in_mongo_a': 1, 'b': 2}}

    def test_dict(self):

        class MySchema(Schema):
            dict = fields.DictField(attribute='in_mongo_dict')

        d = DataProxy(MySchema())
        d.load({'dict': {'a': 1, 'b': {'c': True}}})
        with pytest.raises(KeyError):
            d.in_mongo_dict
        assert d.dump() == {'dict': {'a': 1, 'b': {'c': True}}}
        assert d.dict == {'a': 1, 'b': {'c': True}}
        assert d.to_mongo() == {'in_mongo_dict': {'a': 1, 'b': {'c': True}}}
        # TODO: handle check modif of the dict
        # d.dict['a'] = 1
        # assert d.to_mongo(update=True) == {'$set': {'in_mongo_dict': {'a': 1, 'b': {'c': True}}}}

    def test_embedded_document(self):

        class MyEmbeddedDocument(EmbeddedDocument):
            class Schema(Schema):
                a = fields.IntField(attribute='in_mongo_a')
                b = fields.IntField()

        class MySchema(Schema):
            embedded = fields.EmbeddedField(MyEmbeddedDocument, attribute='in_mongo_embedded')

        d = DataProxy(MySchema())
        d.load({'embedded': {'a': 1, 'b': 2}})
        assert d.dump() == {'embedded': {'a': 1, 'b': 2}}
        assert type(d.embedded) == MyEmbeddedDocument
        assert d.embedded.a == 1
        assert d.embedded.b == 2
        assert d.embedded.dump() == {'a': 1, 'b': 2}
        assert d.embedded.to_mongo() == {'in_mongo_a': 1, 'b': 2}
        assert d.to_mongo() == {'in_mongo_embedded': {'in_mongo_a': 1, 'b': 2}}

        d.embedded = MyEmbeddedDocument(a=2)
        assert d.to_mongo(update=True) == {'$set': {'in_mongo_embedded': {'in_mongo_a': 2}}}

    def test_list(self):

        class MySchema(Schema):
            list = fields.ListField(fields.IntField(), attribute='in_mongo_list')

        d = DataProxy(MySchema())
        d.load({'list': [1, 2, 3]})
        assert d.dump() == {'list': [1, 2, 3]}
        assert d.to_mongo() == {'in_mongo_list': [1, 2, 3]}
        assert d.list == [1, 2, 3]
        d.list.append(4)
        assert d.to_mongo(update=True) == {'$set': {'in_mongo_list': [1, 2, 3, 4]}}

        d.clear_modified()
        d.list = [5, 6, 7]
        assert d.dump() == {'list': [5, 6, 7]}
        assert d.to_mongo(update=True) == {'$set': {'in_mongo_list': [5, 6, 7]}}

        d.clear_modified()
        d.list.pop()
        assert d.dump() == {'list': [5, 6]}
        assert d.to_mongo(update=True) == {'$set': {'in_mongo_list': [5, 6]}}

        d.clear_modified()
        d.list.clear()
        assert d.dump() == {'list': []}
        assert d.to_mongo(update=True) == {'$unset': ['in_mongo_list']}

        d.list = [1, 2, 3]
        d.clear_modified()
        d.list.remove(1)
        assert d.dump() == {'list': [2, 3]}
        assert d.to_mongo(update=True) == {'$set': {'in_mongo_list': [2, 3]}}

        d.clear_modified()
        d.list.reverse()
        assert d.dump() == {'list': [3, 2]}
        assert d.to_mongo(update=True) == {'$set': {'in_mongo_list': [3, 2]}}

        d.clear_modified()
        d.list.sort()
        assert d.dump() == {'list': [2, 3]}
        assert d.to_mongo(update=True) == {'$set': {'in_mongo_list': [2, 3]}}

        d.clear_modified()
        d.list.extend([4, 5])
        assert d.dump() == {'list': [2, 3, 4, 5]}
        assert d.to_mongo(update=True) == {'$set': {'in_mongo_list': [2, 3, 4, 5]}}

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
        assert d.objid == ObjectId("5672d47b1d41c88dcd37ef05")

        d.objid = ObjectId("5672d5e71d41c88f914b77c4")
        d.to_mongo(update=True) == {
            '$set': {'in_mongo_objid': ObjectId("5672d5e71d41c88f914b77c4")}}

        d.objid = ObjectId("5672d5e71d41c88f914b77c4")
        d.to_mongo(update=True) == {
            '$set': {'in_mongo_objid': ObjectId("5672d5e71d41c88f914b77c4")}}

        d.objid = "5672d5e71d41c88f914b77c4"
        assert d.objid == ObjectId("5672d5e71d41c88f914b77c4")

    def test_reference(self):

        class MyReferencedDoc(Document):
            class Schema(Schema):
                pass

        to_refer_doc = MyReferencedDoc.build_from_mongo(
            {'_id': ObjectId("5672d47b1d41c88dcd37ef05")})

        class MySchema(Schema):
            ref = fields.ReferenceField(MyReferencedDoc, attribute='in_mongo_ref')

        d = DataProxy(MySchema())
        d.load({'ref': ObjectId("5672d47b1d41c88dcd37ef05")})
        d.load({'ref': "5672d47b1d41c88dcd37ef05"})
        assert d.dump() == {'ref': "5672d47b1d41c88dcd37ef05"}
        d.ref = to_refer_doc
        assert d.to_mongo(update=True) == {'$set': {'in_mongo_ref': to_refer_doc.pk}}
