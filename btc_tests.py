from mongoengine import *
from models.BtcModels import BtcAddress, BtcTransaction, TxInputAddrInfo, TxOutputAddrInfo
from models.models import AddressTransactionLink
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

def check_otc_conditions(output_tx, change_addr):
    # transaction cannot be a coinbase transaction
    if output_tx.coinbase_tx:
        return False

    tx_input_addrs = set([x.address for x in output_tx.input_addrs])
    tx_output_addrs = set([x.address for x in output_tx.output_addrs])

    # there cannot exist a self-change address (i.e an input address
    # also shows up in the output)
    if tx_input_addrs.intersection(tx_output_addrs):
        return False
    
    # all other output address have been seen before
    for addr in output_tx.output_addrs:
        if addr.address == change_addr:
            continue
        
        addr_links_input = AddressTransactionLink.objects(addr_ref_id=addr.addr_ref_id, 
            addr_used_as_input=True).count()
        addr_links_output = AddressTransactionLink.objects(addr_ref_id=addr.addr_ref_id, 
            addr_used_as_input=False).count()

        if addr_links_input == 0 and addr_links_output <= 1:
            return False

    return True

def compute_otc_stats():
    potential_change_addrs = BtcAddress.objects(neighbor_addrs__size=0).only('addr', 
        'ref_id').limit(1000)
    for addr in potential_change_addrs:
        # print("addr: ", addr.addr)
        num_txs_using_addr_as_input = AddressTransactionLink.objects(addr_ref_id=addr.ref_id, 
            addr_used_as_input=True).count()
        num_txs_using_addr_as_output = AddressTransactionLink.objects(addr_ref_id=addr.ref_id, 
            addr_used_as_input=False).count()

        # print("num input: ", num_txs_using_addr_as_input)
        # print("num output: ", num_txs_using_addr_as_output)

        if num_txs_using_addr_as_input == 0 and num_txs_using_addr_as_output == 1:
            # print("possible OTC")
            output_tx_link = AddressTransactionLink.objects(addr_ref_id=addr.ref_id, 
            addr_used_as_input=False).only('tx_ref_id').first()
            output_tx = BtcTransaction.objects(ref_id=output_tx_link.tx_ref_id).first()
            otc_addr = check_otc_conditions(output_tx, addr.addr)
            if otc_addr:
                print("OTC ADDR!!")
                print("========================")


def test():
    num_addrs = BtcAddress.objects().count()
    print(num_addrs)
        

if __name__ == "__main__":
    # compute_otc_stats()
    test()