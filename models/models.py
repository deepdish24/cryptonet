"""
MongoDB ORM models for Cryptocurrency transactions
"""
from mongoengine import *

class Transaction(Document):
    """
    Data Model for a Cryptocurrency transaction. The primary key (_id) attribute will be 
    assigned in the model that inherits this model
    """
    hash = StringField(primary_key=True)
    time = IntField(required=True)
    block_num = IntField(required=True)
    tx_fees = IntField()
    tx_val = LongField()

    meta = {
        'allow_inheritance': True,
        'indexes': [
            'time'
        ]
    }


class Address(Document):
    """
    Data Model for a Cryptocurrency address
    """
    addr = StringField(primary_key=True)
    time = IntField(required=True) # time address first shows up in blockchain
    curr_wealth = LongField(default=0)
    used_as_input = ListField(StringField(), default=list)
    used_as_output = ListField(StringField(), default=list)

    meta = {
        'allow_inheritance': True,
            'indexes': [
            'curr_wealth',
        ]
    }