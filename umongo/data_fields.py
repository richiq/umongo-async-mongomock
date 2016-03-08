

class Reference:
    def __init__(self, document_cls, oid):
        self._document_cls = document_cls
        self.id = oid
        self._document = None

    def retrieve(self):
        # Sync version
        if not self._document:
            if self.id is None:
                raise ReferenceError('Cannot retrieve a None Reference')
            if isinstance(self._document_cls, str):
                self._document_cls = retrieve_document_cls(self._document_cls)
            self._document = self._document_cls.find_one(self.id)
            if not self._document:
                raise ValidationError(
                    'Reference not found for document %s.' % self._document_cls.__name__)
        return self._document


class List(list):
    pass


class Dict(dict):
    pass
