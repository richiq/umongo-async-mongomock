from .document import Document
from .exceptions import (
    UMongoError,
    ValidationError,
    NoDBDefinedError,
    NotRegisteredDocumentError,
    AlreadyRegisteredDocumentError,
    UpdateError,
    MissingSchemaError,
    NotCreatedError,
    NoCollectionDefinedError,
    FieldNotLoadedError
)
from . import fields
from .schema import BaseSchema, Schema, EmbeddedSchema
from .data_objects import EmbeddedDocument, Reference
from marshmallow import validate


__author__ = 'Emmanuel Leblond'
__email__ = 'emmanuel.leblond@gmail.com'
__version__ = '0.6.0'
__all__ = (
    'Document',
    'EmbeddedDocument',

    'UMongoError',
    'ValidationError',
    'NoDBDefinedError',
    'NotRegisteredDocumentError',
    'AlreadyRegisteredDocumentError',
    'UpdateError',
    'MissingSchemaError',
    'NotCreatedError',
    'NoCollectionDefinedError',
    'FieldNotLoadedError',

    'fields',

    'BaseSchema',
    'Schema',
    'EmbeddedSchema',

    'Reference',

    'validate'
)
