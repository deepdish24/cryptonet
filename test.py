"""
MongoDB Test Read/Write
"""
from mongoengine import *
connect(db='cryptodb')

class TestDoc(Document):
    name = StringField(required=True)
    age = IntField()

test_obj = TestDoc(name="Deepan Saravanan", age=21)
test_obj.save()


