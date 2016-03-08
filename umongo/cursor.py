from pymongo.cursor import Cursor


class Cursor(Cursor):

    def __init__(self, document_cls, cursor, *args, **kwargs):
        self.__dict__['cursor'] = cursor
        self.__dict__['document_cls'] = document_cls
        super().__init__(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self.cursor, name)

    def __setattr__(self, name, value):
        return setattr(self.cursor, name, value)

    def __next__(self):
        n = next(self.cursor)
        return self.document_cls(**n)
