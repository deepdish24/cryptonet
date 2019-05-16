from mongoengine import *
from models.BtcModels import BtcAddress, BtcTransaction, TxInputAddrInfo, TxOutputAddrInfo
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
from btc_functions import (get_tx, get_out_addrs, get_in_addrs, 
    get_raw_tx, coalesce_input_addrs, get_out_addrs_for_inputs)
from btc_crawl import rpc_user, rpc_passwd

'''rpc_connection = AuthServiceProxy("http://%s:%s@127.0.0.1:8332" % (rpc_user, rpc_passwd))'''

def test_addr_neighbors():
    address = "15cE8MYa48tYKdeJg5TEn6VVWuTHeNcZbc"
    addr_obj = BtcAddress.objects(addr=address).first()
    #print("used as input length: ", len(addr_obj.used_as_input))
    #print("used as output length: ", len(addr_obj.used_as_output))
    print("neighbors length: ", len(addr_obj.neighbor_addrs))

def compute_otc_stats():
    potential_change_addrs = BtcAddress.objects(neighbor_addrs__size=0).only('addr', 
        'ref_id')
    # print(len(potential_change_addrs))
    print(len(potential_change_addrs))
    '''for addr in potential_change_addrs:
        if len(addr.used_as_input) == 0 and len(addr.used_as_output) = '''

if __name__ == "__main__":
    compute_otc_stats()