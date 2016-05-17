
def cook_find_filter(doc_cls, filter):
    if doc_cls.opts.is_child:
        filter = filter or {}
        # Current document shares the collection with a parent,
        # we must use the _cls field to discriminate
        if doc_cls.opts.children:
            # Current document has itself children, we also have
            # to search through them
            filter['_cls'] = {'$in': list(doc_cls.opts.children) + [doc_cls.__name__]}
        else:
            filter['_cls'] = doc_cls.__name__
    return filter
