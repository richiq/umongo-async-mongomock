from .abstract import BaseWrappedData, ChangeTracker
from .data_proxy import DataProxy
from .exceptions import ValidationError
from .meta import MetaEmbeddedDocument


__all__ = ('EmbeddedDocument', 'List', 'Reference')


class EmbeddedDocument(DataProxy, metaclass=MetaEmbeddedDocument):

    class Config:
        register_document = False

    def __init__(self, **kwargs):
        schema = self.Schema()
        super().__init__(schema, data=kwargs)


class List(ChangeTracker, list):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._has_changed = False
        self._callback = None

    def has_changed(self):
        return self._has_changed

    def _trigger_change(self):
        self._has_changed = True
        if self._callback:
            self._callback()

    def change_tracker_connect(self, callback):
        self._callback = callback

    def append(self, *args, **kwargs):
        ret = super().append(*args, **kwargs)
        self._trigger_change()
        return ret

    def pop(self, *args, **kwargs):
        ret = super().pop(*args, **kwargs)
        self._trigger_change()
        return ret

    def clear(self, *args, **kwargs):
        ret = super().clear(*args, **kwargs)
        self._trigger_change()
        return ret

    def remove(self, *args, **kwargs):
        ret = super().remove(*args, **kwargs)
        self._trigger_change()
        return ret

    def reverse(self, *args, **kwargs):
        ret = super().reverse(*args, **kwargs)
        self._trigger_change()
        return ret

    def sort(self, *args, **kwargs):
        ret = super().sort(*args, **kwargs)
        self._trigger_change()
        return ret

    def extend(self, *args, **kwargs):
        ret = super().extend(*args, **kwargs)
        self._trigger_change()
        return ret


class Reference(BaseWrappedData):

    def __init__(self, document_cls, pk):
        self.document_cls = document_cls
        self.pk = pk
        self._document = None

    def io_fetch(self):
        # Sync version
        if not self._document:
            if self.pk is None:
                raise ReferenceError('Cannot retrieve a None Reference')
            self._document = self.document_cls.find_one(self.pk)
            if not self._document:
                raise ValidationError(
                    'Reference not found for document %s.' % self._document_cls.__name__)
        return self._document
