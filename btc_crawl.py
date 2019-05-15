from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
from btc_functions import get_tx, get_out_addrs, get_in_addrs, get_raw_tx, coalesce_input_addrs
from models.BtcModels import BtcAddress, BtcTransaction, TxInputAddrInfo, TxOutputAddrInfo
from models.models import AddressTransactionLink
import traceback
import sys

rpc_user = "deepans"
rpc_passwd = "passwd"
# curr_block = 119910
# curr_block = 100000
# curr_block = 0

# Function retrives an address object for the given wallet address.
# If wallet addreass has not been, new object is created
# and returned
def upsert_addr_objects(address_list, address_creation_time, 
    addr_tx_value_dict, is_input_addr, is_coinbase=False):
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

    # create new addresses
    addr_objs = {x.addr: x for x in BtcAddress.objects(addr__in=address_list).only("addr", "ref_id")}

    existing_addrs = [y.addr for x, y in addr_objs.items()]
    addr_ref_ids = [y.ref_id for x, y in addr_objs.items()]

    new_addrs = [y for y in address_list if y not in existing_addrs]
    new_addr_objs = []
    for address in new_addrs:
        addr_obj = BtcAddress(addr=address, time=address_creation_time)
        new_addr_objs.append(addr_obj)

    if new_addr_objs:
        docs = BtcAddress.objects.insert(new_addr_objs)
        for doc in docs:
            addr_objs[doc.addr] = doc
            addr_ref_ids.append(doc.ref_id)
    
    if is_coinbase:
        for address in address_list:
            BtcAddress.objects(addr=address).update_one(inc__curr_wealth=addr_tx_value_dict[address], 
                upsert=False)
    else:
        for address in address_list:
            if is_input_addr:
                ref_id = addr_objs[address].ref_id
                neighbor_addrs = [x for x in addr_ref_ids if x is not ref_id]
                wealth_inc = -1 * addr_tx_value_dict[address]
                BtcAddress.objects(addr=address).update_one(inc__curr_wealth=wealth_inc, 
                    add_to_set__neighbor_addrs=neighbor_addrs, upsert=False)
            else:
                BtcAddress.objects(addr=address).update_one(inc__curr_wealth=addr_tx_value_dict[address], 
                    upsert=False)
    
    return BtcAddress.objects.only("curr_wealth", "ref_id").in_bulk(address_list)

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

    if BtcTransaction.objects(hash=tx_hash).only("hash").first():
        return

    tx = get_raw_tx(tx_hash, rpc_connection)
    out_addrs_dict = dict(get_out_addrs(tx))
    lst_addrs = list(out_addrs_dict.keys())
    addr_dict = upsert_addr_objects(lst_addrs, tx['time'], out_addrs_dict, False, is_coinbase=True)
    
    block_reward = sum(out_addrs_dict.values())
    tx = BtcTransaction(hash=tx_hash, time=tx['time'], block_num=block_num, 
        tx_fees=0, tx_val=block_reward, coinbase_tx=True)
    tx.save()
    tx = BtcTransaction.objects(hash=tx['hash']).only('ref_id').first()

    AddressTransactionLink.objects.insert([AddressTransactionLink(addr_ref_id=x.ref_id, tx_ref_id=tx.ref_id, addr_used_as_input=False) for x in addr_dict.values()])

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

    if BtcTransaction.objects(hash=tx['hash']).only("hash").first():
        return

    out_addrs = tx['out']
    in_addrs = tx['in']

    distinct_inputs_dct = coalesce_input_addrs([(y, z) for x, y, z in in_addrs])
    outputs_dct = dict(out_addrs)

    lst_input_addrs = list(distinct_inputs_dct.keys())
    lst_output_addrs = list(outputs_dct.keys())

    # address to BtcAddress object dict
    wealth_data_input = upsert_addr_objects(lst_input_addrs, tx['time'], 
        distinct_inputs_dct, True)
    wealth_data_output = upsert_addr_objects(lst_output_addrs, tx['time'], 
        outputs_dct, False)


    tx_input_addrs = []
    tx_output_addrs = []


    # retrieve/create BtcAddress objects for tx inputs
    for funding_tx, addr, value in in_addrs:
        addr_obj = wealth_data_input[addr]
        tx_in = TxInputAddrInfo(address=addr, addr_ref_id=addr_obj.ref_id, value=value, 
            wealth=addr_obj.curr_wealth, tx=funding_tx)
        tx_input_addrs.append(tx_in)
    
    # retrieve/create BtcAddress objects for tx outputs
    for addr, value in out_addrs:
        addr_obj = wealth_data_output[addr]
        tx_out = TxOutputAddrInfo(address=addr, addr_ref_id=addr_obj.ref_id, value=value, 
            wealth=addr_obj.curr_wealth - value)
        tx_output_addrs.append(tx_out)
    
    tx_obj = BtcTransaction(hash=tx['hash'], time=tx['time'], 
        block_num=block_num,tx_fees=tx['fees'], tx_val=tx['value'], 
        input_addrs=tx_input_addrs, output_addrs=tx_output_addrs)
    tx_obj.save()
    tx_obj = BtcTransaction.objects(hash=tx['hash']).only('ref_id').first()

    addrs_tx_links_input = [AddressTransactionLink(addr_ref_id=x.ref_id, tx_ref_id=tx_obj.ref_id, 
        addr_used_as_input=True) for x in wealth_data_input.values()]
    addrs_tx_links_output = [AddressTransactionLink(addr_ref_id=x.ref_id, tx_ref_id=tx_obj.ref_id, 
        addr_used_as_input=False) for x in wealth_data_output.values()]

    AddressTransactionLink.objects.insert(addrs_tx_links_input + addrs_tx_links_output, 
        load_bulk=False)


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
            traceback.print_exc()
            sys.exit(1)
            

def crawl(rpc_connection, starting_block=0):
    best_block_hash = rpc_connection.getbestblockhash()
    tgt_block_height = rpc_connection.getblock(best_block_hash)['height']

    while starting_block != tgt_block_height:
        print("Parsing block: ", starting_block)
        parse_block(rpc_connection, starting_block)
        starting_block += 1


def get_next_block_to_parse(rpc_connection):
    """
    Function goes through crawled transaction data and finds the next block to crawl.

    Each time the crawler is started, this function is used to find the next block to
    start crawling at.

    Parameters:
        rpc_connection (RpcConnection object): object allowing for RPC calls to bitcoind daemon

    Returns:
        int: block number of next block to start crawling at
    """
    tx_record = BtcTransaction.objects(coinbase_tx=True).order_by('-ref_id').limit(1).first()

    if not tx_record:
        return 1

    tx = get_raw_tx(tx_record.hash, rpc_connection)
    block_hash = tx['blockhash']
    block_data = rpc_connection.getblock(block_hash)
    return block_data['height']


if __name__ == "__main__":
    rpc_connection = AuthServiceProxy("http://%s:%s@127.0.0.1:8332" % (rpc_user, rpc_passwd))
    next_block = get_next_block_to_parse(rpc_connection)
    crawl(rpc_connection, starting_block=next_block)



'''rpc_connection = AuthServiceProxy("http://%s:%s@127.0.0.1:8332" % (rpc_user, rpc_passwd))
# best_block_hash = rpc_connection.getbestblockhash()
# block = rpc_connection.getblock(best_block_hash)
curr_block = 129878
# curr_block = 100000
block_hash = rpc_connection.getblockhash(curr_block)
block = rpc_connection.getblock(block_hash);
# print(block)
print("Block Hash: ", block['hash'])
transactions = block['tx']

parse_coinbase(transactions[0], rpc_connection, curr_block);

for tx_hash in transactions[1:]:
    tx = get_tx(tx_hash, rpc_connection)
    print(tx['hash'])
    save_to_db(tx, curr_block)
    print("Saved to DB")
    print("-----------------")'''
