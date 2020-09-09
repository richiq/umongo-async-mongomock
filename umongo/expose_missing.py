"""Expose missing context variable

Allows the user to let umongo document return missing rather than None for
empty fields.
"""


from contextvars import ContextVar
from contextlib import AbstractContextManager

EXPOSE_MISSING = ContextVar("expose_missing", default=False)


class ExposeMissing(AbstractContextManager):
    """Let Document expose missing values rather than returning None

    By default, getting a document item returns None if the value is missing.
    Inside this context manager, the missing singleton is returned. This can
    be useful is cases where the user want to distinguish between None and
    missing value.
    """
    def __enter__(self):
        self.token = EXPOSE_MISSING.set(True)

    def __exit__(self, *args, **kwargs):
        EXPOSE_MISSING.reset(self.token)
