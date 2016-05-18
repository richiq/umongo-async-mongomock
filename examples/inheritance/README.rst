Inheritance example
===================

This example demonstrate how inheritance works in μMongo.
It works as a shell on a garage storing different types of vehicles:
cars and motorbikes.

Some examples:

.. code-block::
    $ python examples/inheritance/app.py 
    Welcome to the garage, type `help` if you're lost
    > ls
    Found 3 vehicles
    <object Document __main__.Car({'_id': ObjectId('573c3d0b13adf21b484cf30e'), 'model': 'Chevrolet Impala 1966', 'doors': 5, '_cls': 'Car'})>
    <object Document __main__.Car({'_id': ObjectId('573c3d0b13adf21b484cf30f'), 'model': 'Ford Grand Torino', 'doors': 3, '_cls': 'Car'})>
    <object Document __main__.MotorBike({'_id': ObjectId('573c3d0b13adf21b484cf310'), 'model': 'Honda CB125', 'engine_type': '2-stroke', '_cls': 'MotorBike'})>
    > get 573c3d0b13adf21b484cf30e
    <object Document __main__.Car({'_id': ObjectId('573c3d0b13adf21b484cf30e'), 'model': 'Chevrolet Impala 1966', 'doors': 5, '_cls': 'Car'})>
    > quit
