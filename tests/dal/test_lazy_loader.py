import pytest

from umongo import Document

from .test_pymongo import dep_error as pymongo_dep_error
from .test_txmongo import dep_error as txmongo_dep_error
from .test_motor_asyncio import dep_error as motor_asyncio_dep_error


def lazy_loader_tester(lazy_loader, dal_cls):
    my_collection = object()

    class MyDoc(Document):

        class Meta:
            lazy_collection = lazy_loader(lambda: my_collection)
            register_document = False

    assert MyDoc.Meta.lazy_collection.dal is dal_cls
    assert issubclass(MyDoc, dal_cls)
    MyDoc.collection is my_collection


@pytest.mark.skipif(pymongo_dep_error is not None, reason=pymongo_dep_error)
def test_pymongo_lazy_loader():
    from umongo import pymongo_lazy_loader
    from umongo.dal.pymongo import PyMongoDal
    lazy_loader_tester(pymongo_lazy_loader, PyMongoDal)


@pytest.mark.skipif(txmongo_dep_error is not None, reason=txmongo_dep_error)
def test_txmongo_lazy_loader():
    from umongo import txmongo_lazy_loader
    from umongo.dal.txmongo import TxMongoDal
    lazy_loader_tester(txmongo_lazy_loader, TxMongoDal)


@pytest.mark.skipif(motor_asyncio_dep_error is not None, reason=motor_asyncio_dep_error)
def test_motor_asyncio_lazy_loader():
    from umongo import motor_asyncio_lazy_loader
    from umongo.dal.motor_asyncio import MotorAsyncIODal
    lazy_loader_tester(motor_asyncio_lazy_loader, MotorAsyncIODal)


@pytest.mark.xfail
def test_motor_tornado_lazy_loader():
    from umongo import motor_tornado_lazy_loader
    from umongo.dal.motor_tornado import MotorTornadoDal
    lazy_loader_tester(motor_tornado_lazy_loader, MotorTornadoDal)
