"""
MongoDB ORM models for Bitcoin Transaction Data
"""
from mongoengine import *
from models.models import Transaction, Address

def get_credentials(credentials_file):
    credentials_dict = {}
    with open(credentials_file) as f:
        for line in f.readlines():
            key = line.split("=")[0]
            value = line.split("=")[1][:-1]
            credentials_dict[key] = value
    return credentials_dict

credentials = get_credentials('credentials/mongo_credentials')
connect(
    db='fast_cryptodb', 
    host=credentials['host'], 
    username=credentials['username'], 
    password=credentials['password'], 
    authentication_source='admin'
)

class BtcAddress(Address):
    neighbor_addrs = ListField(IntField(), default=list)


class TxInputAddrInfo(EmbeddedDocument):
    address = LazyReferenceField(BtcAddress)
    addr_ref_id = IntField(required=True)
    value = LongField(required=True)
    wealth = LongField(required=True)
    tx = StringField(required=True)


class TxOutputAddrInfo(EmbeddedDocument):
    address = LazyReferenceField(BtcAddress)
    addr_ref_id = IntField(required=True)
    value = LongField(required=True)
    wealth = LongField(required=True)


class BtcTransaction(Transaction):
    coinbase_tx = BooleanField(default=False)
    input_addrs = ListField(EmbeddedDocumentField(TxInputAddrInfo), default=list)
    output_addrs = ListField(EmbeddedDocumentField(TxOutputAddrInfo), default=list)
