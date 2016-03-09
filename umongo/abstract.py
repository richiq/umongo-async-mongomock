class ChangeTracker:

    def has_changed(self):
        raise NotImplemented()

    def change_tracker_connect(self, callback):
        raise NotImplemented()


class BaseWrappedData:

    def to_mongo(self):
        raise NotImplemented()

    def from_mongo(self, **kwargs):
        raise NotImplemented()

    def dump(self):
        raise NotImplemented()

    def load(self, data):
        raise NotImplemented()


class AbstractCursor:
    # TODO...
    pass
