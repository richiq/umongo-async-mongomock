import pytest
from bson import ObjectId

from .common import BaseTest
from umongo import (Document, Schema, fields, AlreadyRegisteredDocumentError,
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

            class Schema(Schema):
                ref = fields.ReferenceField('DummyDoc')

        with pytest.raises(NotRegisteredDocumentError):
            Doc(ref=ObjectId('56dee8dd1d41c8860b263d86'))

    def test_dont_register_documents(self):

        class Doc(Document):
            pass

        # Should not raise `AlreadyRegisteredDocumentError`
        class Doc(Document):

            class Config:
                register_document = False
