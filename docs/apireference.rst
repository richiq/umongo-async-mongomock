.. _api:

=============
API Reference
=============

.. module:: umongo

Instance
========

.. autoclass:: umongo.instance.Instance
    :members:

.. autoclass:: umongo.frameworks.pymongo.PyMongoInstance

.. autoclass:: umongo.frameworks.txmongo.TxMongoInstance

.. autoclass:: umongo.frameworks.motor_asyncio.MotorAsyncIOInstance

.. autoclass:: umongo.frameworks.mongomock.MongoMockInstance

Document
========

.. autoclass:: umongo.Document

.. autoclass:: umongo.document.DocumentTemplate

.. autoclass:: umongo.document.DocumentOpts

.. autoclass:: umongo.document.DocumentImplementation
    :inherited-members:

EmbeddedDocument
================

.. autoclass:: umongo.EmbeddedDocument

.. autoclass:: umongo.embedded_document.EmbeddedDocumentTemplate

.. autoclass:: umongo.embedded_document.EmbeddedDocumentOpts

.. autoclass:: umongo.embedded_document.EmbeddedDocumentImplementation
    :inherited-members:

MixinDocument
=============

.. autoclass:: umongo.MixinDocument

.. autoclass:: umongo.mixin.MixinDocumentTemplate

.. autoclass:: umongo.mixin.MixinDocumentOpts

.. autoclass:: umongo.mixin.MixinDocumentImplementation
    :inherited-members:

.. _api_abstracts:

Abstracts
=========

.. autoclass:: umongo.abstract.BaseSchema
  :members:

.. autoclass:: umongo.abstract.BaseField
  :members:
  :undoc-members:

.. autoclass:: umongo.abstract.BaseValidator
  :members:

.. autoclass:: umongo.abstract.BaseDataObject
  :members:
  :undoc-members:

.. _api_fields:

Fields
======

.. automodule:: umongo.fields
  :members:
  :undoc-members:

.. _api_data_objects:

Data objects
============

.. automodule:: umongo.data_objects
  :members:
  :undoc-members:

.. _api_marshmallow_intergration:

Marshmallow integration
=======================

.. automodule:: umongo.marshmallow_bonus
  :members:

.. _api_exceptions:

Exceptions
==========

.. automodule:: umongo.exceptions
  :members:
  :undoc-members:
