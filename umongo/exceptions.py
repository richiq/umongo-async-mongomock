"""umongo exceptions"""
from marshmallow import ValidationError  # noqa, republishing


class UMongoError(Exception):
    """Base umongo error"""


class NoCompatibleBuilderError(UMongoError):
    """Can't find builder compatible with database"""


class AbstractDocumentError(UMongoError):
    """Raised when instantiating an abstract document"""


class DocumentDefinitionError(UMongoError):
    """Error in document definition"""


class NoDBDefinedError(UMongoError):
    """No database defined"""


class NotRegisteredDocumentError(UMongoError):
    """Document not registered"""


class AlreadyRegisteredDocumentError(UMongoError):
    """Document already registerd"""


class UpdateError(UMongoError):
    """Error while updating document"""


class DeleteError(UMongoError):
    """Error while deleting document"""


class NotCreatedError(UMongoError):
    """Document does not exist in database"""


class FieldNotLoadedError(UMongoError):
    """Accessing a field not loaded after partial load"""


class NoneReferenceError(UMongoError):
    """Retrieving a None reference"""


class UnknownFieldInDBError(UMongoError):
    """Data from database contains unknown field"""
