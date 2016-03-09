class Singleton:

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<singleton `%s`>' % self.name


not_loaded = Singleton('not_loaded')
undefined = Singleton('undefined')
