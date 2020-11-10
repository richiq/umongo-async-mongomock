"""
Frameworks
==========
"""
from ..exceptions import NoCompatibleBuilderError
from .pymongo import PyMongoBuilder, PyMongoInstance


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

register_builder(PyMongoBuilder)


try:
    from .txmongo import TxMongoBuilder, TxMongoInstance
    register_builder(TxMongoBuilder)
except ImportError:  # pragma: no cover
    pass


try:
    from .motor_asyncio import MotorAsyncIOBuilder, MotorAsyncIOInstance
    register_builder(MotorAsyncIOBuilder)
except ImportError:  # pragma: no cover
    pass


try:
    from .mongomock import MongoMockBuilder, MongoMockInstance
    register_builder(MongoMockBuilder)
except ImportError:  # pragma: no cover
    pass
