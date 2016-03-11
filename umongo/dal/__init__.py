"""
dal
===

Driver Abstraction Layer
"""

from ..exceptions import NoCompatibleDal

# try to load all the dals by default

available_dals = []


try:
    from .pymongo import PyMongoDal
    available_dals.append(PyMongoDal())
except ImportError:
    pass
try:
    from .txmongo import TxMongoDal
    available_dals.append(TxMongoDal())
except ImportError:
    pass
try:
    from .motor_asyncio import MotorAsyncIODal
    available_dals.append(MotorAsyncIODal())
except ImportError:
    pass
try:
    from .motor_tornado import MotorTornadoDal
    available_dals.append(MotorTornadoDal())
except ImportError:
    pass


def find_dal_from_collection(collection):
    for dal in available_dals:
        if dal.is_compatible_with(collection):
            return dal
    raise NoCompatibleDal('Cannot find a umongo dal compatible with %s' %
                          type(collection))
