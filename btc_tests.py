from mongoengine import *
from models.BtcModels import BtcAddress, BtcTransaction, TxInputAddrInfo, TxOutputAddrInfo

connect(db='cryptodb')
address = "1BNwxHGaFbeUBitpjy2AsKpJ29Ybxntqvb"
tx_hash = "fff2525b8931402dd09222c50775608f75787bd2b87e56995a7bdd30f79702c4"

tx = BtcTransaction.objects(hash=tx_hash).first()
print(tx.hash)
print(tx.tx_val)

for addr in tx.input_addrs:
    print("Input address", addr.address.addr)

for addr in tx.output_addrs:
    print("Output address", addr.address.addr)
