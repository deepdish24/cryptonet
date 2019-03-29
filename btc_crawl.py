from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
from hashlib import sha256

def get_txid(raw_tx):
    first_hash = sha256(raw_tx).hexdigest()
    second_hash = sha256(first_hash).hexdigest()
    txid = "".join(reversed(second_hash))
    print(txid)

rpc_user = "deepans"
rpc_passwd = "passwd"

rpc_connection = AuthServiceProxy("http://%s:%s@127.0.0.1:8332" % (rpc_user, rpc_passwd))
best_block_hash = rpc_connection.getbestblockhash()
block = rpc_connection.getblock(best_block_hash)

print(block["tx"][1])

tx_hash = block["tx"][1]

tx_raw = rpc_connection.getrawtransaction(tx_hash)
get_txid(tx_raw)
#tx_info = rpc_connection.gettransaction(tx_raw)
#print(tx_info)
