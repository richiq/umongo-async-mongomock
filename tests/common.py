from umongo.registerer import default_registerer


class BaseTest:

    def setup(self):
        default_registerer.documents = {}
