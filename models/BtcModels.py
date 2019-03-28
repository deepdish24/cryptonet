"""
MongoDB ORM models for Bitcoin Transaction Data
"""
from mongoengine import *
connect(db='cryptodb')

class Transaction(Document):
    pass