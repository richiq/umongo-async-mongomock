from .mongomock import (
    MongoMockBuilder,
    MongoMockDocument,
    MongoMockInstance,
    WrappedCursor,
)


class AsyncMongoMockDocument(MongoMockDocument):
    __slots__ = ()
    cursor_cls = WrappedCursor
    opts = MongoMockDocument.opts

    async def reload(self):
        """
        Retrieve and replace document's data by the ones in database.

        Raises :class:`umongo.exceptions.NotCreatedError` if the document
        doesn't exist in database.
        """
        return super().reload()

    async def commit(self, io_validate_all=False, conditions=None, replace=False):
        """
        Commit the document in database.
        If the document doesn't already exist it will be inserted, otherwise
        it will be updated.

        :param io_validate_all: Validate all field instead of only changed ones.
        :param conditions: Only perform commit if matching record in db
            satisfies condition(s) (e.g. version number).
            Raises :class:`umongo.exceptions.UpdateError` if the
            conditions are not satisfied.
        :param replace: Replace the document rather than update.
        :return: A :class:`pymongo.results.UpdateResult` or
            :class:`pymongo.results.InsertOneResult` depending of the operation.
        """
        return super().commit(io_validate_all, conditions, replace)

    async def delete(self, conditions=None):
        """
        Remove the document from database.

        :param conditions: Only perform delete if matching record in db
            satisfies condition(s) (e.g. version number).
            Raises :class:`umongo.exceptions.DeleteError` if the
            conditions are not satisfied.
        Raises :class:`umongo.exceptions.NotCreatedError` if the document
        is not created (i.e. ``doc.is_created`` is False)
        Raises :class:`umongo.exceptions.DeleteError` if the document
        doesn't exist in database.

        :return: A :class:`pymongo.results.DeleteResult`
        """
        return super().delete(conditions)

    @classmethod
    async def find_one(cls, filter=None, *args, **kwargs):
        """
        Find a single document in database.
        """
        return super().find_one(filter, *args, **kwargs)

    @classmethod
    async def find(cls, filter=None, *args, **kwargs):
        """
        Find a list document in database.

        Returns a cursor that provide Documents.
        """
        return super().find(filter, *args, **kwargs)

    @classmethod
    async def count_documents(cls, filter=None, **kwargs):
        """
        Get the number of documents in this collection.

        Unlike pymongo's collection.count_documents, filter is optional and
        defaults to an empty filter.
        """
        return super().count_documents(filter, **kwargs)

    @classmethod
    async def ensure_indexes(cls):
        """
        Check&create if needed the Document's indexes in database
        """
        return super().ensure_indexes()


class AsyncMongoMockBuilder(MongoMockBuilder):
    BASE_DOCUMENT_CLS = AsyncMongoMockDocument


class AsyncMongoMockInstance(MongoMockInstance):
    """
    :class:`umongo.instance.Instance` implementation for mongomock
    """
    BUILDER_CLS = AsyncMongoMockBuilder
