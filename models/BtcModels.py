"""
MongoDB ORM models for Bitcoin Transaction Data
"""
from mongoengine import *
from models import Transaction, Address

class BtcAddress(Address):
    neighbor_addrs = ListField(ReferenceField(BtcAddress))


class TxInputAddrInfo(EmbeddedDocument):
    address = ReferenceField(BtcAddress)
    value = IntField(required=True)
    wealth = IntField(required=True)
    tx = IntField(required=True)


class TxOutputAddrInfo(EmbeddedDocument):
    address = ReferenceField(BtcAddress)
    value = IntField(required=True)
    wealth = IntField(required=True)


class BtcTransaction(Transaction):
    input_addrs = ListField(EmbeddedDocumentField(TxInputAddrInfo))
    output_addrs = ListField(EmbeddedDocumentField(TxOutputAddrInfo))