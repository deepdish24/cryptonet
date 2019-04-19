from mongoengine import *
from models.BtcModels import BtcAddress, BtcTransaction, TxInputAddrInfo, TxOutputAddrInfo
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
from btc_functions import (get_tx, get_out_addrs, get_in_addrs, 
    get_raw_tx, coalesce_input_addrs, get_out_addrs_for_inputs)
from btc_crawl import rpc_user, rpc_passwd

'''rpc_connection = AuthServiceProxy("http://%s:%s@127.0.0.1:8332" % (rpc_user, rpc_passwd))

address = "1BNwxHGaFbeUBitpjy2AsKpJ29Ybxntqvb"
tx_hash = "8ebe1df6ebf008f7ec42ccd022478c9afaec3ca0444322243b745aa2e317c272"
funding_tx = "5492a05f1edfbd29c525a3dbf45f654d0fc45a805ccd620d0a4dff47de63f90b"

lst = ["1JyDazZuKP6CqYGhqcQurLM5AWZmn9RRGs"]

result = BtcAddress.objects.only("addr").in_bulk(lst)
print(result)
print(result["1JyDazZuKP6CqYGhqcQurLM5AWZmn9RRGs"].curr_wealth)
#result = BtcAddress.objects(addr=lst[0]).update_one(set__curr_wealth=102, push__used_as_input="testhere2", full_result=True)
#print(result.raw_result)'''

for addr in BtcAddress.objects.all():
    if len(addr.neighbor_addrs) > 0:
        print("address: ", addr.addr)
        print("neighbors: ", addr.neighbor_addrs);
        break


'''tx = BtcTransaction.objects(hash=tx_hash).first()
print(tx.hash)
print(tx.tx_val)

addrs = [x.address.addr for x in tx.input_addrs]
addrs.append("deepan")
print(addrs)

dct = BtcAddress.objects.in_bulk(addrs)
for object_id, addr in dct.items():
    print(object_id + ", " + str(addr.curr_wealth))'''

'''tx = get_raw_tx(tx_hash, rpc_connection)
get_in_addrs(tx, rpc_connection)'''

'''tx = get_raw_tx(funding_tx, rpc_connection)
out_addrs = get_out_addrs_for_inputs(tx)
print(tx['vout'])
print("===============")
print(out_addrs)'''