"""
dal
===

Driver Abstraction Layer
"""

from ..exceptions import NoCompatibleDalError
from ..abstract import BaseLazyLoader
from importlib import import_module


__all__ = (
    'DalRegisterer',

    'default_dal_registerer',
    'register_dal',
    'unregister_dal',
    'find_dal_from_db',

    'pymongo_lazy_loader',
    'txmongo_lazy_loader',
    'motor_asyncio_lazy_loader',
    'motor_tornado_lazy_loader',
    'mongomock_lazy_loader'
)


class DalRegisterer:
    """
    Keep trace of the defined class::`umongo.Document` children.
    This is usefull to retrieve a document class from it name to avoid
    recursive referencing and tricky imports.
    """

    def __init__(self):
        self._dals = set()

    def register(self, dal):
        self._dals.add(dal)

    def unregister(self, dal):
        """
        Basically only used for tests
        """
        self._dals.remove(dal)

    def find_from_db(self, db):
        for dal in self._dals:
            if dal.is_compatible_with(db):
                return dal
        raise NoCompatibleDalError('Cannot find a umongo dal compatible with %s' % db)


default_dal_registerer = DalRegisterer()
register_dal = default_dal_registerer.register
unregister_dal = default_dal_registerer.unregister
find_dal_from_db = default_dal_registerer.find_from_db


def lazy_loader_factory(get_dal_cls):
    """
    Create a lazy loader for the given DAL. Lazy loader should be used
    when the collection to use with a document is not available when the
    document is defined

    >>> class MyDoc(Document):
    ...     class Meta:
    ...         lazy_collection = pymongo_lazy_loader(lambda: init_db().my_doc)
    """

    class LazyLoader(BaseLazyLoader):

        def __init__(self, loader):
            # Load the dal only when used to avoid import error
            # when the dal's requirements are not met
            self._dal = get_dal_cls()
            self._loader = loader

        @property
        def dal(self):
            return self._dal

        def load(self):
            return self._loader()

    return LazyLoader


pymongo_lazy_loader = lazy_loader_factory(
    lambda: import_module('umongo.dal.pymongo').PyMongoDal)
txmongo_lazy_loader = lazy_loader_factory(
    lambda: import_module('umongo.dal.txmongo').TxMongoDal)
motor_asyncio_lazy_loader = lazy_loader_factory(
    lambda: import_module('umongo.dal.motor_asyncio').MotorAsyncIODal)
motor_tornado_lazy_loader = lazy_loader_factory(
    lambda: import_module('umongo.dal.motor_tornado').MotorTornadoDal)
mongomock_lazy_loader = lazy_loader_factory(
    lambda: import_module('umongo.dal.mongomock').MongoMockDal)


# try to load all the dals by default
try:
    from .pymongo import PyMongoDal
    register_dal(PyMongoDal)
except ImportError:  # pragma: no cover
    raise
    pass
try:
    from .txmongo import TxMongoDal
    register_dal(TxMongoDal)
except ImportError:  # pragma: no cover
    pass
try:
    from .motor_asyncio import MotorAsyncIODal
    register_dal(MotorAsyncIODal)
except ImportError:  # pragma: no cover
    pass
try:
    from .motor_tornado import MotorTornadoDal
    register_dal(MotorTornadoDal)
except ImportError:  # pragma: no cover
    pass
try:
    from .mongomock import MongoMockDal
    register_dal(MongoMockDal)
except ImportError:  # pragma: no cover
    pass
