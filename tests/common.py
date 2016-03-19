from bson import ObjectId
from umongo.registerer import default_registerer


class BaseTest:

    def setup(self):
        default_registerer.documents = {}


def get_pymongo_version():
    import pymongo
    version = getattr(pymongo, '__version__', None) or getattr(pymongo, 'version')
    version = [int(i) for i in version.split('.')]
    if len(version) == 2:
        version.append(0)
    return version
