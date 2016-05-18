import re
from copy import copy
from marshmallow.fields import Field

from .document import Document, DocumentOpts, DocumentImplementation
from .exceptions import NoCollectionDefinedError, DocumentDefinitionError, NotRegisteredDocumentError
from .schema import Schema, EmbeddedSchema, on_need_add_id_field, add_child_field
from .abstract import AbstractDal
from .indexes import parse_index


def camel_to_snake(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def _is_child(bases):
    """Find if the given inheritance leeds to a child document (i.e.
    a document that shares the same collection with a parent)
    """
    return next((True for b in bases
                 if issubclass(b, DocumentImplementation) and not b.opts.abstract), False)


def _collect_fields(nmspc):
    """Split dict between fields and non-fields elements"""
    schema_nmspc = {}
    doc_nmspc = {}
    for key, item in nmspc.items():
        if isinstance(item, Field):
            schema_nmspc[key] = item
        else:
            doc_nmspc[key] = item
    return doc_nmspc, schema_nmspc


def _collect_indexes(nmspc, bases):
    """
    Retrieve all indexes (custom defined in meta class, by inheritances
    and unique attribut in fields)
    """
    meta = nmspc.get('Meta')
    indexes = []
    is_child = _is_child(bases)

    # First collect parent indexes (including inherited field's unique indexes)
    for base in bases:
        if issubclass(base, DocumentImplementation):
            indexes += base.opts.indexes

    # Then get our own custom indexes
    if is_child:
        custom_indexes = [parse_index(x, base_compound_field='_cls')
                   for x in getattr(meta, 'indexes', ())]
    else:
        custom_indexes = [parse_index(x) for x in getattr(meta, 'indexes', ())]
    indexes += custom_indexes

    if is_child:
        indexes.append(parse_index('_cls'))

    # Finally parse our own fields (i.e. not inherited) for unique indexes
    def parse_field(mongo_path, path, field):
        if field.unique:
            index = {'unique': True, 'key': [mongo_path]}
            if not field.required or field.allow_none:
                index['sparse'] = True
            if is_child:
                index['key'].append('_cls')
            indexes.append(parse_index(index))

    for name, field in _collect_fields(nmspc)[1].items():
        parse_field(name or field.attribute, name, field)
        if hasattr(field, 'map_to_field'):
            field.map_to_field(name or field.attribute, name, parse_field)

    return indexes


def _build_document_opts(instance, template, name ,nmspc, bases):
    kwargs = {}
    meta = nmspc.get('Meta')
    collection_name = getattr(meta, 'collection_name', None)
    kwargs['instance'] = instance
    kwargs['template'] = template
    kwargs['abstract'] = getattr(meta, 'abstract', False)
    kwargs['allow_inheritance'] = getattr(meta, 'allow_inheritance', None)
    kwargs['base_schema_cls'] = getattr(meta, 'base_schema_cls', Schema)
    kwargs['indexes'] = _collect_indexes(nmspc, bases)
    kwargs['is_child'] = _is_child(bases)

    # Handle option inheritance and integrity checks
    for base in bases:
        if not issubclass(base, Document):
            continue
        popts = base.opts
        # Notify the parent of it newborn !
        popts.children.add(name)
        if not popts.allow_inheritance:
            raise DocumentDefinitionError("Document %r doesn't allow inheritance" % base)
        if kwargs['abstract'] and not popts.abstract:
            raise DocumentDefinitionError(
                "Abstract document should have all it parents abstract")
        if popts.collection_name:
            if collection_name:
                raise DocumentDefinitionError(
                    "Cannot redefine collection_name in a child, use abstract instead")
            collection_name = popts.collection_name

    if collection_name:
        if kwargs['abstract']:
            raise DocumentDefinitionError(
                'Abstract document cannot define collection_name')
    elif not kwargs['abstract']:
        # Determine the collection name from the class name
        collection_name = camel_to_snake(name)

    return DocumentOpts(collection_name=collection_name, **kwargs)


class BaseBuilder:

    BASE_DOCUMENT_CLS = None

    def __init__(self, instance):
        assert self.BASE_DOCUMENT_CLS
        self.instance = instance
        self._templates_lookup = {Document: self.BASE_DOCUMENT_CLS}

    def _convert_bases(self, bases):
        "Replace template parents by their implementation inside this instance"
        converted_bases = []
        for base in bases:
            assert not issubclass(base, DocumentImplementation), \
                'Document cannot inherit of implementations'
            if issubclass(base, Document):
                if base not in self._templates_lookup:
                    raise NotRegisteredDocumentError('Unknown document `%s`' % base)
                converted_bases.append(self._templates_lookup[base])
            else:
                converted_bases.append(base)
        return tuple(converted_bases)

    def _build_schema(self, doc_template, schema_bases, schema_nmspc):
        """
        Overload this function to customize schema
        """

        # Set the instance to all fields
        from .fields import ListField, EmbeddedField

        def patch_field(field):
            field.instance = self.instance
            if isinstance(field, ListField):
                patch_field(field.container)
            if isinstance(field, EmbeddedField):
                for embedded_field in field.schema.fields.values():
                    patch_field(embedded_field)

        for field in schema_nmspc.values():
            patch_field(field)

        # Finally build the schema class
        return type('%sSchema' % doc_template.__name__, schema_bases, schema_nmspc)

    def build_from_template(self, doc_template):
        assert issubclass(doc_template, Document)
        name = doc_template.__name__
        bases = self._convert_bases(doc_template.__bases__)
        opts = _build_document_opts(self.instance, doc_template, name, doc_template.__dict__, bases)
        nmspc, schema_template_fields = _collect_fields(doc_template.__dict__)
        nmspc['opts'] = opts

        # Given the fields provided by the template are going to be
        # customized in the implementation, we copy them to avoid
        # overwriting if two implementations are created
        schema_nmspc = {k: copy(v) for k, v in schema_template_fields.items()}
        # Create schema by retrieving inherited schema classes
        schema_bases = tuple([base.Schema for base in bases
                              if hasattr(base, 'Schema')])
        if not schema_bases:
            schema_bases = (Schema, )
        on_need_add_id_field(schema_bases, schema_nmspc)
        # If Document is a child, _cls field must be added to the schema
        if opts.is_child:
            add_child_field(name, schema_nmspc)
        schema_cls = self._build_schema(doc_template, schema_bases, schema_nmspc)
        nmspc['Schema'] = schema_cls
        nmspc['schema'] = schema_cls()

        doc_cls = type(name, bases, nmspc)
        self._templates_lookup[doc_template] = doc_cls
        return doc_cls
