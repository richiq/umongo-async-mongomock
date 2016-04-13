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
from .dal import (
    pymongo_lazy_loader,
    txmongo_lazy_loader,
    motor_asyncio_lazy_loader,
    motor_tornado_lazy_loader
)
from . import fields
from .schema import BaseSchema, Schema, EmbeddedSchema
from .data_objects import EmbeddedDocument, Reference
from marshmallow import validate


__author__ = 'Emmanuel Leblond'
__email__ = 'emmanuel.leblond@gmail.com'
__version__ = '0.6.1'
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

    'pymongo_lazy_loader',
    'txmongo_lazy_loader',
    'motor_asyncio_lazy_loader',
    'motor_tornado_lazy_loader',

    'fields',

    'BaseSchema',
    'Schema',
    'EmbeddedSchema',

    'Reference',

    'validate'
)
