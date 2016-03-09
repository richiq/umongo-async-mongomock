from ..exceptions import NoCompatibleDriver

# try to load all the drivers by default

available_drivers = []


try:
    from .pymongo import PyMongoDriver
    available_drivers.append(PyMongoDriver)
except ImportError:
    pass
try:
    from .txmongo import TxMongoDriver
    available_drivers.append(TxMongoDriver)
except ImportError:
    pass
try:
    from .motor_asyncio import MotorAsyncIODriver
    available_drivers.append(MotorAsyncIODriver)
except ImportError:
    pass
try:
    from .motor_tornado import MotorTornadoDriver
    available_drivers.append(MotorTornadoDriver)
except ImportError:
    pass


def find_driver_from_collection(collection):
    for driver in available_drivers:
        if driver.is_compatible_with(collection):
            return driver
    raise NoCompatibleDriver('Cannot find a umongo driver compatible with %s' %
                             type(collection))
