from datetime import datetime

from umongo import *


class TestDocument:

    def test_create(self):

        class Student(Document):
            id = fields.ObjectId(dump_only=True, attribute='_id')
            name = fields.Str(required=True)
            birthday = fields.DateTime()

            class Config:
                collection = db.student

        john = Student(name='John Doe', birthday=datetime(1995, 12, 12))
        john.to_mongo() == {'_id': john.data['_id'], 'name': 'John Doe', 'birthday': datetime(1995, 12, 12)}
