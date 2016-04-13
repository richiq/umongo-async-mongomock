.. _tutorial:

========
Tutorial
========

Base concepts
=============


In μMongo 3 worlds are considered:

.. figure:: data_flow.png
   :alt: data flow in μMongo


Client world
------------

This is the data from outside μMongo, it can be JSON dict from your web framework
(i.g. ``request.get_json()`` with `flask <http://flask.pocoo.org/>`_ or
``json.loads(request.raw_post_data)`` in `django <https://www.djangoproject.com/>`_)
or it could be regular Python dict with Python-typed data

JSON dict example

.. code-block:: python

    >>> {"str_field": "hello world", "int_field": 42, "date_field": "2015-01-01T00:00:00Z"}

Python dict example

.. code-block:: python

    >>> {"str_field": "hello world", "int_field": 42, "date_field": datetime(2015, 1, 1)}

To be integrated into μMongo, those data need to be unserialized. Same thing
to leave μMongo they need to be serialized (under the hood
μMongo uses `marshmallow <http://marshmallow.readthedocs.org/>`_ schema).
The unserialization operation is done automatically when instantiating a
:class:`umongo.Document`. The serialization is done when calling
:meth:`umongo.Document.dump` on a document instance.


Object Oriented world
---------------------

So what's good about :class:`umongo.Document` ? Well it's allow you to work
with your data as Objects and to guarantee there validity against a model.

First define a document with few :mod:`umongo.fields`

.. code-block:: python

    class Dog(Document):
        name = fields.StrField(required=True)
        breed = fields.StrField(missing="Mongrel")
        birthday = fields.DateTimeField()

Note that each field can be customized with special attributes like
``required`` (which is pretty self-explanatory) or ``missing`` (if the
field is missing it will take this value).

Now we can take play back and forth between OO and client worlds

.. code-block:: python

    >>> client_data = {'name': 'Odwin', 'birthday': '2001-09-22T00:00:00Z'}
    >>> odwin = Dog(**client_data)
    >>> odwin.breed
    "Mongrel"
    >>> odwin.birthday
    datetime.datetime(2001, 9, 22, 0, 0)
    >>> odwin.breed = "Labrador"
    >>> odwin.dump()
    {'birthday': '2001-09-22T00:00:00+00:00', 'breed': 'Labrador', 'name': 'Odwin'}

.. note:: You can access the data as attribute (i.g. ``odwin.name``) or as item (i.g. ``odwin['name']``).
          The latter is specially useful if one of your field name clash with :class:`umongo.Document`'s attributes.

OO world enforces model validation for each modification

.. code-block:: python

    >>> odwin.bad_field = 42
    [...]
    AttributeError: bad_field
    >>> odwin.birthday = "not_a_date"
    [...]
    ValidationError: Not a valid datetime.

.. note: Just one exception: ``required`` attribute is validate at insertion time, we'll talk about that later.

Object orientation means inheritance, of course you can do that

.. code-block:: python

    class Animal(Document):
        breed = fields.StrField()
        birthday = fields.DateTimeField()

        class Meta:
            allow_inheritance = True
            abstract = True

    class Dog(Animal):
        name = fields.StrField(required=True)

    class Duck(Animal):
        pass

Note the ``Meta`` subclass, it is used (along with inherited Meta classes)
to configure the document class, you can access this final config through
the ``opts`` attribute.
Here we use this to allow ``Animal`` to be inheritable and to make it abstract.

.. code-block:: python

    >>> Animal.opts
    <DocumentOpts(abstract=True, allow_inheritance=True, is_child=False, base_schema_cls=<class 'umongo.schema.Schema'>, indexes=[], custom_indexes=[], collection=None, lazy_collection=None, dal=None, children={'Duck', 'Dog'})>
    >>> NotAllowedSubDog.opts
    <DocumentOpts(abstract=False, allow_inheritance=False, is_child=False, base_schema_cls=<class 'umongo.schema.Schema'>, indexes=[], custom_indexes=[], collection=None, lazy_collection=None, dal=None, children={})>
    >>> class NotAllowedSubDog(Dog): pass
    [...]
    DocumentDefinitionError: Document <class '__main__.Dog'> doesn't allow inheritance
    >>> Animal(breed="Mutant")
    [...]
    AbstractDocumentError: Cannot instantiate an abstract Document



Mongo world
-----------

What the point of a MongoDB ODM without MongoDB ? So here it is !

Mongo world consist of data returned in a format comprehensible by a mongodb
driver (`pymongo <https://api.mongodb.org/python/current/>`_ for instance).

.. code-block:: python

    >>> odwin.to_mongo()
    {'birthday': datetime.datetime(2001, 9, 22, 0, 0), 'name': 'Odwin'}

Well it our case the data haven't change much (if any !). Let's consider something more complex:

.. code-block:: python

    class Dog(Document):
        name = fields.StrField(attribute='_id')

Here we use decide to use the name of the dog as our ``_id`` key, but for
readability we keep it as ``name`` inside our document.

.. code-block:: python

    >>> odwin = Dog(name='Odwin')
    >>> odwin.dump()
    {'name': 'Odwin'}
    >>> odwin.to_mongo()
    {'_id': 'Odwin'}
    >>> Dog.build_from_mongo({'_id': 'Scruffy'}).dump()
    {'name': 'Scruffy'}

But what about if we what to retrieve the ``_id`` field whatever it name is ?
No problem, use the ``pk`` attribute:

.. code-block:: python

    >>> odwin.pk
    'Odwin'
    >>> Duck().pk
    None

Ok so now we got our data in a way we can insert it to MongoDB through our favorite driver.
In fact most of the time you don't need to use ``to_mongo`` directly.
Instead you should configure (remember the ``Meta`` class ?) you document class
with a collection to insert into:

.. code-block:: python

    >>> db = pymongo.MongoClient().umongo_test
    >>> class Dog(Document):
    ...     name = fields.StrField(attribute='_id')
    ...     breed = fields.StrField(missing="Mongrel")
    ...     class Meta:
    ...         collection = db.dog

.. note::
    Often in more complex applications you won't have your driver ready
    when defining your documents. In such case you should use instead ``lazy_collection``
    with a lazy loader depending of your driver:

    .. code-block:: python

          def get_collection():
              return txmongo.MongoConnection()['lazy_db_doc']

          class LazyDBDoc(Document):
              class Meta:
                  lazy_collection = txmongo_lazy_loader(get_collection)


This way you will be able to ``commit`` your changes into the database:

.. code-block:: python

    >>> odwin = Dog(name='Odwin', breed='Labrador')
    >>> odwin.commit()

You get also access to Object Oriented version of your driver methods:

.. code-block:: python

    >>> Dog.find()
    <umongo.dal.pymongo.WrappedCursor object at 0x7f169851ba68>
    >>> next(Dog.find())
    <object Document __main__.Dog({'_id': 'Odwin', 'breed': 'Labrador'})>
    Dog.find_one({'_id': 'Odwin'})
    <object Document __main__.Dog({'_id': 'Odwin', 'breed': 'Labrador'})>
 
For the moment all examples has been done with pymongo, but thing are
pretty the same with other drivers:

.. code-block:: python

    >>> db = motor.motor_asyncio.AsyncIOMotorClient()['umongo_test']
    >>> class Dog(Document):
    ...     name = fields.StrField(attribute='_id')
    ...     breed = fields.StrField(missing="Mongrel")
    ...     class Meta:
    ...         collection = db.dog

Of course the way you'll be calling methods will differ:

.. code-block:: python

    >>> odwin = Dog(name='Odwin', breed='Labrador')
    >>> yield from odwin.commit()
    >>> dogs = yield from Dog.find()

.. note:: Be careful not to mix documents with different collection type
          defined or unexpected thing could happened (and furthermore there is no
          practical reason to do that !)
