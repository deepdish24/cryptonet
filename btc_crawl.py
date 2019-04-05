from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
from btc_functions import get_tx, get_out_addrs, get_in_addrs, get_raw_tx
from models.BtcModels import BtcAddress, BtcTransaction, TxInputAddrInfo, TxOutputAddrInfo
from hashlib import sha256

rpc_user = "deepans"
rpc_passwd = "passwd"
curr_block = 100000

def parse_coinbase(tx_hash, rpc_connection):
    tx = get_raw_tx(tx_hash, rpc_connection)
    out_addrs = get_out_addrs(tx)
    print("Coinbase Outs: ", out_addrs)

def save_to_db(tx):
    out_addrs = tx['out']
    in_addrs = tx['in']

    in_addr_objs = []
    out_addr_objs = []

    tx_input_addrs = []
    tx_output_addrs = []

    for addr, value in in_addrs:
        addr_obj = BtcAddress(addr=addr, time=tx['time'])
        in_addr_objs.append(addr_obj)
        tx_in = TxInputAddrInfo(address=addr_obj, value=value, 
            wealth=addr_obj.curr_wealth, tx=tx['hash'])
        tx_input_addrs.append(tx_in)
    
    for addr, value in out_addrs:
        addr_obj = BtcAddress(addr=addr, time=tx['time'])
        out_addr_objs.append(addr_obj)
        tx_out = TxOutputAddrInfo(address=addr_obj, value=value, 
            wealth=addr_obj.curr_wealth)
        tx_output_addrs.append(tx_out)

    for addr_obj in in_addr_objs:
        neighbor_lst = [x for x in in_addr_objs if x is not addr_obj]
        addr_obj.neighbor_addrs = neighbor_lst
    
    for addr_obj in in_addr_objs:
        addr_obj.save()
    
    for addr_obj in out_addr_objs:
        addr_obj.save()
    
    tx_obj = BtcTransaction(hash=tx['hash'], time=tx['time'], 
        block_num=curr_block,tx_fees=tx['fees'], tx_val=tx['value'], 
        input_addrs=tx_input_addrs, output_addrs=tx_output_addrs)
    tx_obj.save()

rpc_connection = AuthServiceProxy("http://%s:%s@127.0.0.1:8332" % (rpc_user, rpc_passwd))
# best_block_hash = rpc_connection.getbestblockhash()
# block = rpc_connection.getblock(best_block_hash)

block_hash = rpc_connection.getblockhash(curr_block)
block = rpc_connection.getblock(block_hash);
print("Block Hash: ", block['hash'])
transactions = block['tx']

parse_coinbase(transactions[0], rpc_connection);

for tx_hash in transactions[1:]:
    tx = get_tx(tx_hash, rpc_connection)
    print(tx['hash'])
    print(tx)
    save_to_db(tx)
    print("Saved to DB")
    print("-----------------")


'''tx_hash = "7ce0a971cf6af300dbd4be8f4a077ee0cdfbbf74a11804b8ac06a71b7c2f386a"
print(tx_hash)
print("=========================")
tx = get_tx(tx_hash, rpc_connection)
print(tx)'''
