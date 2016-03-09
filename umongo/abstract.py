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


class BaseDriver:
    pass


class BaseField:

    # def _serialize(self, value, attr, obj):

    # def _deserialize(self, value, attr, data):

    def _serialize_to_mongo(self, value):
        return value

    def _deserialize_from_mongo(self, value):
        return value

    def get_default():
        pass
