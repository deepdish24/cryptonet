from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
from btc_functions import get_tx, get_out_addrs, get_in_addrs, get_raw_tx
# from models.BtcModels import BtcAddress, BtcTransaction, TxInputAddrInfo, TxOutputAddrInfo
from hashlib import sha256

rpc_user = "deepans"
rpc_passwd = "passwd"
curr_block = 100000

def parse_coinbase(tx_hash, rpc_connection):
    tx = get_raw_tx(tx_hash, rpc_connection)
    out_addrs = get_out_addrs(tx)
    print("Coinbase Outs: ", out_addrs)

rpc_connection = AuthServiceProxy("http://%s:%s@127.0.0.1:8332" % (rpc_user, rpc_passwd))
# best_block_hash = rpc_connection.getbestblockhash()
# block = rpc_connection.getblock(best_block_hash)

'''block_hash = rpc_connection.getblockhash(curr_block)
block = rpc_connection.getblock(block_hash);
print("Block Hash: ", block['hash'])
transactions = block['tx']

parse_coinbase(transactions[0], rpc_connection);

for tx_hash in transactions[1:]:
    tx = get_tx(tx_hash, rpc_connection)
    print(tx)
    print("-----------------")'''


# tx_hash = block["tx"][1]
tx_hash = "7ce0a971cf6af300dbd4be8f4a077ee0cdfbbf74a11804b8ac06a71b7c2f386a"
print(tx_hash)
print("=========================")
tx = get_tx(tx_hash, rpc_connection)
print(tx)
