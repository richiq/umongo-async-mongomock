from abc import ABCMeta, abstractstaticmethod, abstractmethod


class AbstractDal(metaclass=ABCMeta):

    @abstractstaticmethod
    def is_compatible_with(collection):
        pass

    @abstractmethod
    def reload(self, doc):
        pass

    @abstractmethod
    def commit(self, doc, io_validate_all=False):
        pass

    @abstractmethod
    def delete(self, doc):
        pass

    @abstractmethod
    def find_one(self, doc_cls, *args, **kwargs):
        pass

    @abstractmethod
    def find(self, doc_cls, *args, **kwargs):
        pass


class AbstractCursor:
    # TODO...
    pass


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
