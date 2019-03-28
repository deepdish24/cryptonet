"""
MongoDB Test Read/Write
"""
from mongoengine import *
connect(db='cryptodb')

class TestDoc(Document):
    _id = StringField(required=True)
    name = StringField(required=True)
    age = IntField()
    meta = {
        'indexes': [
            '#name'
        ]
    }


test_obj = TestDoc(_id="cool", name="Kavin Saravanan", age=16)
test_obj.save()
# test_obj = TestDoc(name="Deepan Saravanan", age=21)
# test_obj.save()
#test_obj = next(TestDoc.objects(name="Deepan Saravanan"))
#print(test_obj.name +  ", " + str(test_obj.age))

