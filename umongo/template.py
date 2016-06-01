class Implementation:
    pass


class Template:
    def __init__(self, *args, **kwargs):
        raise NotImplementedError('Cannot instantiate a template, '
                                  'use instance.register result instead.')


class MetaTemplate(type):

    def __new__(cls, name, bases, nmspc):
        # If user has passed parent documents as implementation, we need
        # to retrieve the original templates
        cooked_bases = []
        for base in bases:
            if issubclass(base, Implementation):
                base = base.opts.template
            cooked_bases.append(base)
        if not cooked_bases:
            cooked_bases.append(Template)
        return type.__new__(cls, name, tuple(cooked_bases), nmspc)

    def __repr__(cls):
        return "<Template class '%s.%s'>" % (cls.__module__, cls.__name__)

class MetaImplementation(MetaTemplate):

    def __new__(cls, name, bases, nmspc):
        # `opts` is only defined by the builder to implement a template.
        # If this field is missing, the user is subclassing an implementation
        # to define a new type of document, thus we should construct a template class.
        if 'opts' not in nmspc:
            # Inheritance to avoid metaclass conflicts
            return super().__new__(cls, name, bases, nmspc)
        else:
            return type.__new__(cls, name, bases, nmspc)

    def __repr__(cls):
        return "<Implementation class '%s.%s'>" % (cls.__module__, cls.__name__)
