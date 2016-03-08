from marshmallow import Schema


class Schema(Schema):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # TODO: set id field if doesn't exists
        # TODO: set missing fields to None
