from .exceptions import AlreadyRegisteredDocumentError, NotRegisteredDocumentError


class DocumentRegisterer:

    def __init__(self):
        self.documents = {}

    def register(self, doc):
        name = doc.__name__
        previous_doc = self.documents.get(name)
        if previous_doc:
            raise AlreadyRegisteredDocumentError(
                'Document `%s` has already registerer as %r' % (name, previous_doc))
        self.documents[name] = doc

    def retrieve(self, name):
        doc = self.documents.get(name)
        if not doc:
            raise NotRegisteredDocumentError(
                "Document `%s` hasn't been registered" % name)
        return doc


default_registerer = DocumentRegisterer()
register_document = default_registerer.register
retrieve_document = default_registerer.retrieve
