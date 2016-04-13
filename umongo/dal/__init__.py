"""
dal
===

Driver Abstraction Layer
"""

from ..exceptions import NoCompatibleDalError
from importlib import import_module


__all__ = (
    'DalRegisterer',

    'default_dal_registerer',
    'register_dal',
    'unregister_dal',
    'find_dal_from_collection',

    'pymongo_lazy_loader',
    'txmongo_lazy_loader',
    'motor_asyncio_lazy_loader',
    'motor_tornado_lazy_loader'
)


class DalRegisterer:

    def __init__(self):
        self._dals = set()

    def register(self, dal):
        self._dals.add(dal)

    def unregister(self, dal):
        """
        Basically only used for tests
        """
        self._dals.remove(dal)

    def find_from_collection(self, collection):
        for dal in self._dals:
            if dal.is_compatible_with(collection):
                return dal
        raise NoCompatibleDalError('Cannot find a umongo dal compatible with %s' %
                                   type(collection))


default_dal_registerer = DalRegisterer()
register_dal = default_dal_registerer.register
unregister_dal = default_dal_registerer.unregister
find_dal_from_collection = default_dal_registerer.find_from_collection


def lazy_loader_factory(get_dal_cls):
    """Create a lazy loader for the given DAL. Lazy loader should be used
    when the collection to use with a document is not available when the
    document is defined

    >>> class MyDoc(Document):
    ...     class Meta:
    ...         lazy_collection = pymongo_lazy_loader(lambda: init_db().my_doc)
    """

    class LazyLoader:

        def __init__(self, loader):
            # Load the dal only when used to avoid import error
            # when the dal's requirements are not met
            self.dal = get_dal_cls()
            self.loader = loader

        def load(self):
            return self.loader()

    return LazyLoader


pymongo_lazy_loader = lazy_loader_factory(
    lambda: import_module('umongo.dal.pymongo').PyMongoDal)
txmongo_lazy_loader = lazy_loader_factory(
    lambda: import_module('umongo.dal.txmongo').TxMongoDal)
motor_asyncio_lazy_loader = lazy_loader_factory(
    lambda: import_module('umongo.dal.motor_asyncio').MotorAsyncIODal)
motor_tornado_lazy_loader = lazy_loader_factory(
    lambda: import_module('umongo.dal.motor_tornado').MotorTornadoDal)


# try to load all the dals by default
try:
    from .pymongo import PyMongoDal
    register_dal(PyMongoDal)
except ImportError:
    pass
try:
    from .txmongo import TxMongoDal
    register_dal(TxMongoDal)
except ImportError:
    pass
try:
    from .motor_asyncio import MotorAsyncIODal
    register_dal(MotorAsyncIODal)
except ImportError:
    pass
try:
    from .motor_tornado import MotorTornadoDal
    register_dal(MotorTornadoDal)
except ImportError:
    pass
