from .abstract import AbstractCursor


class Cursor(AbstractCursor):

    def __init__(self, document_cls, cursor, *args, **kwargs):
        self.__dict__['raw_cursor'] = cursor
        self.__dict__['document_cls'] = document_cls
        super().__init__(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self.__dict__['raw_cursor'], name)

    def __setattr__(self, name, value):
        return setattr(self.raw_cursor, name, value)

    def __next__(self):
        elem = next(self.raw_cursor)
        return self.document_cls.build_from_mongo(elem)

    def __iter__(self):
        for elem in self.raw_cursor:
            yield self.document_cls.build_from_mongo(elem)
