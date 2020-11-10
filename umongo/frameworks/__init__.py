"""
Frameworks
==========
"""
from ..exceptions import NoCompatibleBuilderError
from ..instance import LazyLoaderInstance
from .pymongo import PyMongoBuilder


__all__ = (
    'BuilderRegisterer',

    'default_builder_registerer',
    'register_builder',
    'unregister_builder',
    'find_builder_from_db',

    'PyMongoInstance',
    'TxMongoInstance',
    'MotorAsyncIOInstance',
    'MongoMockInstance'
)


class BuilderRegisterer:

    def __init__(self):
        self.builders = []

    def register(self, builder):
        if builder not in self.builders:
            # Insert new item first to overload older compatible builders
            self.builders.insert(0, builder)

    def unregister(self, builder):
        # Basically only used for tests
        self.builders.remove(builder)

    def find_from_db(self, db):
        for builder in self.builders:
            if builder.is_compatible_with(db):
                return builder
        raise NoCompatibleBuilderError(
            'Cannot find a umongo builder compatible with %s' % type(db))


default_builder_registerer = BuilderRegisterer()
register_builder = default_builder_registerer.register
unregister_builder = default_builder_registerer.unregister
find_builder_from_db = default_builder_registerer.find_from_db


# Define lazy loader instances for each builder

class PyMongoInstance(LazyLoaderInstance):
    """
    :class:`umongo.instance.LazyLoaderInstance` implementation for pymongo
    """
    BUILDER_CLS = PyMongoBuilder


register_builder(PyMongoBuilder)


try:
    from .txmongo import TxMongoBuilder
    register_builder(TxMongoBuilder)

    class TxMongoInstance(LazyLoaderInstance):
        """
        :class:`umongo.instance.LazyLoaderInstance` implementation for txmongo
        """
        BUILDER_CLS = TxMongoBuilder

except ImportError:  # pragma: no cover
    pass


try:
    from .motor_asyncio import MotorAsyncIOBuilder
    register_builder(MotorAsyncIOBuilder)

    class MotorAsyncIOInstance(LazyLoaderInstance):
        """
        :class:`umongo.instance.LazyLoaderInstance` implementation for motor-asyncio
        """
        BUILDER_CLS = MotorAsyncIOBuilder

except ImportError:  # pragma: no cover
    pass


try:
    from .mongomock import MongoMockBuilder
    register_builder(MongoMockBuilder)

    class MongoMockInstance(LazyLoaderInstance):
        """
        :class:`umongo.instance.LazyLoaderInstance` implementation for mongomock
        """
        BUILDER_CLS = MongoMockBuilder

except ImportError:  # pragma: no cover
    pass
