import pymongo
from bson import ObjectId
from umongo.registerer import default_registerer


TEST_DB = 'umongo_test'


# Use a sync driver for easily drop the test database
con = pymongo.MongoClient()


class BaseTest:

    def setup(self):
        con.drop_database('test_db')
        default_registerer.documents = {}


def get_pymongo_version():
    version = getattr(pymongo, '__version__', None) or getattr(pymongo, 'version')
    version = [int(i) for i in version.split('.')]
    if len(version) == 2:
        version.append(0)
    return version
