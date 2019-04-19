"""
MongoDB ORM models for Bitcoin Transaction Data
"""
from mongoengine import *
from models.models import Transaction, Address

def get_db_credentials(credentials_file):
    with open(credentials_file) as f:
        username = f.readline()[:-1]
        password = f.readline()[:-1]
    return (username, password)

username, password = get_db_credentials('credentials/mongo_credentials')

connect(db='cryptodb', username=username, password=password, authentication_source='admin')

class BtcAddress(Address):
    neighbor_addrs = ListField(IntField(), default=list)


class TxInputAddrInfo(EmbeddedDocument):
    address = IntField()
    value = LongField(required=True)
    wealth = LongField(required=True)
    tx = StringField(required=True)


class TxOutputAddrInfo(EmbeddedDocument):
    address = IntField()
    value = LongField(required=True)
    wealth = LongField(required=True)


class BtcTransaction(Transaction):
    coinbase_tx = BooleanField(default=False)
    input_addrs = ListField(EmbeddedDocumentField(TxInputAddrInfo), default=list)
    output_addrs = ListField(EmbeddedDocumentField(TxOutputAddrInfo), default=list)
