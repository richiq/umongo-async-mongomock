"""
dal
===

Driver Abstraction Layer
"""

from ..exceptions import NoCompatibleDal


class DalRegisterer:

    def __init__(self):
        self._dals = []

    def register(self, dal):
        self._dals.append(dal)

    def find_from_collection(self, collection):
        for dal in self._dals:
            if dal.is_compatible_with(collection):
                return dal
        raise NoCompatibleDal('Cannot find a umongo dal compatible with %s' %
                              type(collection))


default_dal_registerer = DalRegisterer()
register_dal = default_dal_registerer.register
find_dal_from_collection = default_dal_registerer.find_from_collection

# try to load all the dals by default

try:
    from .pymongo import PyMongoDal
    register_dal(PyMongoDal())
except ImportError:
    pass
try:
    from .txmongo import TxMongoDal
    register_dal(TxMongoDal())
except ImportError:
    pass
try:
    from .motor_asyncio import MotorAsyncIODal
    register_dal(MotorAsyncIODal())
except ImportError:
    pass
try:
    from .motor_tornado import MotorTornadoDal
    register_dal(MotorTornadoDal())
except ImportError:
    pass
