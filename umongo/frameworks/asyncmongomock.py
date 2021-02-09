from inspect import iscoroutine
from pymongo.errors import DuplicateKeyError
import marshmallow as ma

from ..exceptions import NotCreatedError, UpdateError
from ..query_mapper import map_query
from .motor_asyncio import SESSION
from .mongomock import (
    MongoMockBuilder,
    MongoMockDocument,
    MongoMockInstance,
    WrappedCursor as MongoMockCursor,
)


class WrappedCursor(MongoMockCursor):
    __slots__ = ()

    def __anext__(self):
        try:
            return self.__next__()
        except StopIteration:
            raise StopAsyncIteration

    def __aiter__(self):
        return self


class AsyncMongoMockDocument(MongoMockDocument):
    __slots__ = ()
    cursor_cls = WrappedCursor
    opts = MongoMockDocument.opts

    async def __coroutined_pre_insert(self):
        ret = self.pre_insert()
        if iscoroutine(ret):
            ret = await ret
        return ret

    async def __coroutined_pre_update(self):
        ret = self.pre_update()
        if iscoroutine(ret):
            ret = await ret
        return ret

    async def __coroutined_pre_delete(self):
        ret = self.pre_delete()
        if iscoroutine(ret):
            ret = await ret
        return ret

    async def __coroutined_post_insert(self, ret):
        ret = self.post_insert(ret)
        if iscoroutine(ret):
            ret = await ret
        return ret

    async def __coroutined_post_update(self, ret):
        ret = self.post_update(ret)
        if iscoroutine(ret):
            ret = await ret
        return ret

    async def __coroutined_post_delete(self, ret):
        ret = self.post_delete(ret)
        if iscoroutine(ret):
            ret = await ret
        return ret

    async def __aiter__(self):
        return self

    async def __anext__(self):
        return self.__next__()

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
        try:
            if self.is_created:
                if self.is_modified() or replace:
                    query = conditions or {}
                    query["_id"] = self.pk
                    # pre_update can provide additional query filter and/or
                    # modify the fields' values
                    additional_filter = await self.__coroutined_pre_update()
                    if additional_filter:
                        query.update(map_query(additional_filter, self.schema.fields))
                    self.required_validate()
                    await self.io_validate(validate_all=io_validate_all)
                    if replace:
                        payload = self._data.to_mongo(update=False)
                        ret = self.collection.replace_one(
                            query, payload, session=SESSION.get()
                        )
                    else:
                        payload = self._data.to_mongo(update=True)
                        ret = self.collection.update_one(
                            query, payload, session=SESSION.get()
                        )
                    if ret.matched_count != 1:
                        raise UpdateError(ret)
                    await self.__coroutined_post_update(ret)
                else:
                    ret = None
            elif conditions:
                raise NotCreatedError(
                    "Document must already exist in database to use `conditions`."
                )
            else:
                await self.__coroutined_pre_insert()
                self.required_validate()
                await self.io_validate(validate_all=io_validate_all)
                payload = self._data.to_mongo(update=False)
                ret = self.collection.insert_one(payload, session=SESSION.get())
                # TODO: check ret ?
                self._data.set(self.pk_field, ret.inserted_id)
                self.is_created = True
                await self.__coroutined_post_insert(ret)
        except DuplicateKeyError as exc:
            # Sort value to make testing easier for compound indexes
            keys = sorted(exc.details["keyPattern"].keys())
            try:
                fields = [self.schema.fields[k] for k in keys]
            except KeyError:
                # A key in the index is unknwon from umongo
                raise exc
            if len(keys) == 1:
                msg = fields[0].error_messages["unique"]
                raise ma.ValidationError({keys[0]: msg})
            raise ma.ValidationError(
                {
                    k: f.error_messages["unique_compound"].format(fields=keys)
                    for k, f in zip(keys, fields)
                }
            )
        self._data.clear_modified()
        return ret

    async def delete(self, conditions=None):
        """
        Alias of :meth:`remove` to enforce default api.
        """
        return await self.remove(conditions=conditions)

    async def remove(self, conditions=None):
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

        :return: Delete result dict returned by underlaying driver.
        """
        if not self.is_created:
            raise NotCreatedError("Document doesn't exists in database")
        query = conditions or {}
        query["_id"] = self.pk
        # pre_delete can provide additional query filter
        additional_filter = await self.__coroutined_pre_delete()
        if additional_filter:
            query.update(map_query(additional_filter, self.schema.fields))
        ret = self.collection.delete_one(query, session=SESSION.get())
        if ret.deleted_count != 1:
            raise DeleteError(ret)
        self.is_created = False
        await self.__coroutined_post_delete(ret)
        return ret

    async def io_validate(self, validate_all=False):
        return super().io_validate(validate_all=False)

    @classmethod
    async def find_one(cls, filter=None, *args, **kwargs):
        """
        Find a single document in database.
        """
        return super().find_one(filter, *args, **kwargs)

    @classmethod
    def find(cls, filter=None, *args, **kwargs):
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
