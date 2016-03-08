class UMongoError(Exception):
    pass


class ValidationError(UMongoError):
    pass


class NoDBDefinedError(UMongoError):
    pass


class NotRegisteredDocumentError(UMongoError):
    pass


class AlreadyRegisteredDocumentError(UMongoError):
    pass


class SchemaFieldNamingClashError(UMongoError):
    pass


class UpdateError(UMongoError):
    pass
