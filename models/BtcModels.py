"""
MongoDB ORM models for Bitcoin Transaction Data
"""
from mongoengine import *
from models.models import Transaction, Address
connect(db='cryptodb')

class BtcAddress(Address):
    neighbor_addrs = ListField(ReferenceField(Address))


class TxInputAddrInfo(EmbeddedDocument):
    address = ReferenceField(BtcAddress)
    value = IntField(required=True)
    wealth = IntField(required=True)
    tx = StringField(required=True)


class TxOutputAddrInfo(EmbeddedDocument):
    address = ReferenceField(BtcAddress)
    value = IntField(required=True)
    wealth = IntField(required=True)


class BtcTransaction(Transaction):
    input_addrs = ListField(EmbeddedDocumentField(TxInputAddrInfo))
    output_addrs = ListField(EmbeddedDocumentField(TxOutputAddrInfo))
