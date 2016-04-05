from itertools import zip_longest

from umongo.indexes import (
    parse_index, explicit_key, parse_index,
    IndexModel, ASCENDING, DESCENDING, TEXT, HASHED)
from umongo import Document, fields


def assert_indexes(indexes1, indexes2):
    if hasattr(indexes1, '__iter__'):
        for e1, e2 in zip_longest(indexes1, indexes2):
            assert e1, "missing index %s" % e2.document
            assert e2, "too much indexes: %s" % e1.document
            assert e1.document == e2.document
    else:
        assert indexes1.document == indexes2.document


class TestIndexes:

    def test_parse_index(self):
        for value, expected in (
                ('my_index', IndexModel([('my_index', ASCENDING)])),
                ('+my_index', IndexModel([('my_index', ASCENDING)])),
                ('-my_index', IndexModel([('my_index', DESCENDING)])),
                ('$my_index', IndexModel([('my_index', TEXT)])),
                ('#my_index', IndexModel([('my_index', HASHED)])),
                # Compound indexes
                (('index1', '-index2'), IndexModel([('index1', ASCENDING), ('index2', DESCENDING)])),
                # No changes if not needed
                (IndexModel([('my_index', ASCENDING)]), IndexModel([('my_index', ASCENDING)])),
                # Custom index
                ({
                    'name': 'my-custom-index',
                    'key': ['+index1', '-index2'],
                    'sparse': True,
                    'unique': True,
                    'expireAfterSeconds': 42
                },
                IndexModel([('index1', ASCENDING), ('index2', DESCENDING)],
                           name='my-custom-index', sparse=True,
                           unique=True, expireAfterSeconds=42)
                ),
            ):
            assert_indexes(parse_index(value), expected)

    def test_explicit_key(self):
        for value, expected in (
                ('my_index', ('my_index', ASCENDING)),
                ('+my_index', ('my_index', ASCENDING)),
                ('-my_index', ('my_index', DESCENDING)),
                ('$my_index', ('my_index', TEXT)),
                ('#my_index', ('my_index', HASHED)),
                # No changes if not needed
                (('my_index', ASCENDING), ('my_index', ASCENDING)),
            ):
            assert explicit_key(value) == expected

    def test_inheritance(self):

        class Parent(Document):
            last_name = fields.StrField()

            class Meta:
                allow_inheritance = True
                indexes = ['last_name']

        class Child(Parent):
            first_name = fields.StrField()

            class Meta:
                indexes = ['-first_name']

        assert_indexes(Parent.opts.indexes, [IndexModel([('last_name', ASCENDING)])])
        assert_indexes(Child.opts.indexes,
            [
                IndexModel([('last_name', ASCENDING)]),
                IndexModel([('first_name', DESCENDING), ('_cls', ASCENDING)]),
                IndexModel([('_cls', ASCENDING)])
            ])
