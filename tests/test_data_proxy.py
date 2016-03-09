from marshmallow import ValidationError
import pytest

from umongo.data_proxy import DataProxy
from umongo import Schema, fields


class TestDataProxy:

    def test_simple(self):

        class MySchema(Schema):
            a = fields.IntField()
            b = fields.IntField()

        d = DataProxy(MySchema())
        d.load({'a': 1, 'b': 2})
        assert d.a == 1
        d.b = 3
        assert d.b == 3
        assert d._data == {'a': 1, 'b': 3}
        d['a'] = 4
        assert d['a'] == 4
        assert d.a == d['a']
        assert d.dump() == {'a': 4, 'b': 3}
        del d.b
        assert d.dump() == {'a': 4}

    def test_load(self):

        class MySchema(Schema):
            a = fields.IntField()
            b = fields.IntField(attribute='in_mongo_b')

        d = DataProxy(MySchema())
        d.load({'a': 1, 'b': 2})
        assert d.to_mongo() == {'a': 1, 'in_mongo_b': 2}

        d.a = 3
        assert d.to_mongo(update=True) == {'$set': {'a': 3}}

        d.load({'a': 4, 'b': 5})
        assert d.to_mongo(update=True) is None
        assert d.to_mongo() == {'a': 4, 'in_mongo_b': 5}

    def test_modify(self):

        class MySchema(Schema):
            a = fields.IntField()
            b = fields.IntField(attribute='in_mongo_b')

        d = DataProxy(MySchema())
        d.load({'a': 1, 'b': 2})
        assert d.to_mongo() == {'a': 1, 'in_mongo_b': 2}
        assert d.to_mongo(update=True) is None
        d.a = 3
        del d.b
        assert d.to_mongo(update=True) == {'$set': {'a': 3}, '$unset': ['in_mongo_b']}
        d.clear_modified()
        assert d.to_mongo(update=True) is None
        assert d.to_mongo() == {'a': 3}

    def test_set(self):

        class MySchema(Schema):
            a = fields.IntField()
            b = fields.IntField(attribute='in_mongo_b')

        d = DataProxy(MySchema())
        d.load({'a': 1, 'b': 2})
        d.a = 3
        assert d.to_mongo() == {'a': 3, 'in_mongo_b': 2}
        assert d.to_mongo(update=True) == {'$set': {'a': 3}}

        d.load({'a': 1, 'b': 2})
        d.b = 3
        assert d.to_mongo() == {'a': 1, 'in_mongo_b': 3}
        assert d.to_mongo(update=True) == {'$set': {'in_mongo_b': 3}}

    def test_del(self):

        class MySchema(Schema):
            a = fields.IntField()
            b = fields.IntField(attribute='in_mongo_b')

        d = DataProxy(MySchema())
        d.load({'a': 1, 'b': 2})
        del d.b
        assert d.to_mongo() == {'a': 1}
        assert d.to_mongo(update=True) == {'$unset': ['in_mongo_b']}
        del d.a
        assert d.to_mongo(update=True) == {'$unset': ['a', 'in_mongo_b']}

    def test_item(self):

        class MySchema(Schema):
            a = fields.IntField()
            b = fields.IntField()

        d = DataProxy(MySchema())
        d.load({'a': 1, 'b': 2})
        d['a'] = 2
        assert d.to_mongo() == {'a': 2, 'b': 2}
        assert d.to_mongo(update=True) == {'$set': {'a': 2}}
        assert d['a'] == d.a == 2
        del d['a']
        assert d.to_mongo() == {'b': 2}
        assert d.to_mongo(update=True) == {'$unset': ['a']}

    def test_route_naming(self):

        class MySchema(Schema):
            in_front = fields.IntField(attribute='in_mongo')

        d = DataProxy(MySchema())
        with pytest.raises(ValidationError):
            d.load({'in_mongo': 42})
        d.load({'in_front': 42})
        with pytest.raises(KeyError):
            d.in_mongo
        assert d.in_front == 42
        d.in_front = 24
        assert d._data == {'in_mongo': 24}
        assert d.in_front == 24
        assert d.dump() == {'in_front': 24}
        assert d.to_mongo() == {'in_mongo': 24}

    def test_from_mongo(self):

        class MySchema(Schema):
            in_front = fields.IntField(attribute='in_mongo')

        d = DataProxy(MySchema())
        with pytest.raises(KeyError):
            d.from_mongo({'in_front': 42})
        d.from_mongo({'in_mongo': 42})
        assert d.in_front == 42
