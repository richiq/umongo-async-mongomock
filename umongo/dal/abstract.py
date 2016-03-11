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
