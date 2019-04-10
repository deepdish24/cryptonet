from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
from btc_functions import get_tx, get_out_addrs, get_in_addrs, get_raw_tx, coalesce_input_addrs
from models.BtcModels import BtcAddress, BtcTransaction, TxInputAddrInfo, TxOutputAddrInfo
import sys

rpc_user = "deepans"
rpc_passwd = "passwd"
# curr_block = 119910
# curr_block = 100000
# curr_block = 0

# Function retrives an address object for the given wallet address.
# If wallet addreass has not been, new object is created
# and returned
def get_addr_object(address, address_creation_time, 
    tx_hash, addr_tx_value, is_input_addr, is_coinbase=False):
    """
    Function retrives an address object for the given wallet address.
    If wallet address has not been seen, new object is created
    and returned

    Parameters:
        address (str): bitcoin wallet address
        address_creation_time (int): time of transaction (used if address is created)
        tx_hash (str): hash of transaction
        addr_wealth_at_tx (int): amount of money being sent by address
        is_input_addr (bool): boolean indicating if address is in input of tx or in output of tx

    Returns:
        BtcAddress: Function returns a BtcAddress object representing the address record in MongoDB
                    database
    """

    if BtcTransaction.objects(hash=tx_hash).first():
        return

    addr_obj = BtcAddress.objects(addr=address).first()
    if not addr_obj:
        addr_obj = BtcAddress(addr=address, time=address_creation_time)
    
    if is_coinbase:
        addr_obj.curr_wealth += addr_tx_value
        addr_obj.used_as_output.append(tx_hash)
        return addr_obj

    if is_input_addr:
        addr_obj.used_as_input.append(tx_hash)
        addr_obj.curr_wealth = max(0, addr_obj.curr_wealth - addr_tx_value)
    else:
        addr_obj.used_as_output.append(tx_hash)
        addr_obj.curr_wealth += addr_tx_value
    
    return addr_obj

def parse_coinbase(tx_hash, rpc_connection, block_num):
    """
    Function to correctly parse the coinbase of each transaction. 
    
    The output wallet address of the coinbase is created if it has not been seen yet
    and updated in wealth based on the block reward. The record is then saved to the
    database

    Parameters:
        tx_hash (str): transaction hash of coinbase
        rpc_connection (RpcConnection object): object allowing for RPC calls to bitcoind daemon

    Returns:
        void: Function simply creates/updates BtcAddress record and stores it in MongoDB database

    """

    if BtcTransaction.objects(hash=tx_hash).first():
        return

    tx = get_raw_tx(tx_hash, rpc_connection)
    out_addrs = get_out_addrs(tx)
    output_addr, block_reward = out_addrs.pop()

    addr_obj = get_addr_object(output_addr, tx['time'], 
        tx_hash, block_reward, False, is_coinbase=True)
    addr_obj.save()

    tx = BtcTransaction(hash=tx_hash, time=tx['time'], block_num=block_num, 
        tx_fees=0, tx_val=block_reward, coinbase_tx=True)
    tx.save()


def save_to_db(tx, block_num):
    """
    Function to correctly parse transaciton information, update existing records
    with new information, and save all updates to the MongoDB database. 

    Parameters:
        tx (dict): transaction data parsed into a dictionary by 
                    get_tx in btc_functions.py

    Returns:
        void: Funciton stores new records/updates to records in database
    """

    out_addrs = tx['out']
    in_addrs = tx['in']

    distinct_inputs_dct = coalesce_input_addrs([(y, z) for x, y, z in in_addrs])

    # address to BtcAddress object dict
    distinct_in_addrs = {}
    out_addr_objs = []

    tx_input_addrs = []
    tx_output_addrs = []


    # retrieve/create BtcAddress objects for tx inputs
    for funding_tx, addr, value in in_addrs:
        if addr not in distinct_in_addrs:
            curr_wealth = distinct_inputs_dct[addr]
            addr_obj = get_addr_object(addr, tx['time'], tx['hash'], curr_wealth, True)
            distinct_in_addrs[addr] = addr_obj

        tx_in = TxInputAddrInfo(address=distinct_in_addrs[addr], value=value, 
            wealth=addr_obj.curr_wealth, tx=funding_tx)
        tx_input_addrs.append(tx_in)
    
    # retrieve/create BtcAddress objects for tx outputs
    for addr, value in out_addrs:
        addr_obj = get_addr_object(addr, tx['time'], tx['hash'], value, False)
        out_addr_objs.append(addr_obj)
        tx_out = TxOutputAddrInfo(address=addr_obj, value=value, 
            wealth=addr_obj.curr_wealth - value)
        tx_output_addrs.append(tx_out)

    # populate neighbors list for BtcAddress objects in distinct_in_addrs
    lst_input_addresses = distinct_in_addrs.values()
    for addr_obj in lst_input_addresses:
        neighbor_lst = [x.addr for x in lst_input_addresses if x is not addr_obj]
        curr_neighbors = set(addr_obj.neighbor_addrs)
        addr_obj.neighbor_addrs = list(curr_neighbors.union(neighbor_lst))
    
    # save input and output BtcAddress objects
    for addr_obj in distinct_in_addrs.values():
        addr_obj.save()

    for addr_obj in out_addr_objs:
        addr_obj.save()
    
    tx_obj = BtcTransaction(hash=tx['hash'], time=tx['time'], 
        block_num=block_num,tx_fees=tx['fees'], tx_val=tx['value'], 
        input_addrs=tx_input_addrs, output_addrs=tx_output_addrs)
    tx_obj.save()

def parse_block(rpc_connection, block_num):
    block_hash = rpc_connection.getblockhash(block_num)
    block = rpc_connection.getblock(block_hash)
    transactions = block['tx']

    parse_coinbase(transactions[0], rpc_connection, block_num)

    for tx_hash in transactions[1:]:
        tx = get_tx(tx_hash, rpc_connection)
        try:
            save_to_db(tx, block_num)
        except Exception as e:
            print("Exception occured while parsing tx: ", tx['hash'])
            print(e)
            sys.exit(1)
            

def crawl(starting_block=0):
    rpc_connection = AuthServiceProxy("http://%s:%s@127.0.0.1:8332" % (rpc_user, rpc_passwd))
    best_block_hash = rpc_connection.getbestblockhash()
    tgt_block_height = rpc_connection.getblock(best_block_hash)['height']

    while starting_block != tgt_block_height:
        print("Parsing block: ", starting_block)
        parse_block(rpc_connection, starting_block)
        starting_block += 1


if __name__ == "__main__":
    starting_block = int(sys.argv[1])
    crawl(starting_block=starting_block)



'''rpc_connection = AuthServiceProxy("http://%s:%s@127.0.0.1:8332" % (rpc_user, rpc_passwd))
# best_block_hash = rpc_connection.getbestblockhash()
# block = rpc_connection.getblock(best_block_hash)

block_hash = rpc_connection.getblockhash(curr_block)
block = rpc_connection.getblock(block_hash);
print(block)
print("Block Hash: ", block['hash'])
transactions = block['tx']

parse_coinbase(transactions[0], rpc_connection);

for tx_hash in transactions[1:]:
    tx = get_tx(tx_hash, rpc_connection)
    print(tx['hash'])
    save_to_db(tx)
    print("Saved to DB")
    print("-----------------")'''
