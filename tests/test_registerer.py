import pytest
from bson import ObjectId

from .common import BaseTest
from umongo import (Document, fields, AlreadyRegisteredDocumentError,
                    NotRegisteredDocumentError)


class TestRegisterDocuments(BaseTest):

    def test_already_register_documents(self):

        class Doc(Document):
            pass

        with pytest.raises(AlreadyRegisteredDocumentError):

            class Doc(Document):
                pass

    def test_not_register_documents(self):

        class Doc(Document):
            ref = fields.ReferenceField('DummyDoc')

        with pytest.raises(NotRegisteredDocumentError):
            Doc(ref=ObjectId('56dee8dd1d41c8860b263d86'))

    def test_dont_register_documents(self):

        class Doc(Document):
            pass

        # Should not raise `AlreadyRegisteredDocumentError`
        class Doc(Document):

            class Meta:
                register_document = False
