try:
    from pymongo import IndexModel
except ImportError:
    # Pymong < 3 used by motor doesn't support IndexModel
    class IndexModel:
        def __init__(self, keys, **kwargs):
            if not isinstance(keys, (list, tuple)):
                keys = [keys]
            kwargs['key'] = {k: d for k, d in keys}
            self.document = kwargs
from pymongo import ASCENDING, DESCENDING, TEXT, HASHED


def explicit_index(index):
    if isinstance(index, (list, tuple)):
        assert len(index) == 2, 'Must be a (`key`, `direction`) tuple'
        return index
    elif index.startswith('+'):
        return (index[1:], ASCENDING)
    elif index.startswith('-'):
        return (index[1:], DESCENDING)
    elif index.startswith('$'):
        return (index[1:], TEXT)
    elif index.startswith('#'):
        return (index[1:], HASHED)
    else:
        return (index, ASCENDING)


def parse_index(index, base_compound_field=None):
    keys = None
    args = {}
    if isinstance(index, IndexModel):
        keys = [(k, d) for k, d in index.document['key'].items()]
        args = {k: v for k, v in index.document.items() if k != 'key'}
    elif isinstance(index, (tuple, list)):
        # Compound indexes
        keys = [explicit_index(e) for e in index]
    elif isinstance(index, str):
        keys = [explicit_index(index)]
    elif isinstance(index, dict):
        assert 'fields' in index, 'Index passed as dict must have a fields entry'
        keys = [explicit_index(e) for e in index['fields']]
        args = {k: v for k, v in index.items() if k != 'fields'}
    else:
        raise TypeError('Index type must be <str>, <list>, <dict> or <pymongo.IndexModel>')
    if base_compound_field:
        keys.append(explicit_index(base_compound_field))
    print(index, '------->', IndexModel(keys, **args).document)
    return IndexModel(keys, **args)
