from bitcoinrpc.authproxy import JSONRPCException
btc_unit = 100000000

def get_tx(tx_hash, rpc_connection):
    """
    Function returns dictionary containing transaction information that is further parsed and
    stored in database. Further parsing involves updating address objects to include neighbor
    addresses for clustering as well as updating the current wealth of addresses

    Parameters:
        tx_hash (str): hash of transaction to be parsed
        rpc_connection (RpcConnection object): object allowing for RPC calls to bitcoind daemon

    Returns:
        dict: dictionary containing transaction information
    """

    try:
        tx = rpc_connection.getrawtransaction(tx_hash, True)
    except JSONRPCException:
        return []
    
    tx_struct = {}
    tx_struct['hash'] = tx['txid']
    tx_struct['time'] = tx['time']
    tx_struct['out'] = get_out_addrs(tx)
    tx_struct['in'] = get_in_addrs(tx, rpc_connection)

    total_out = sum([y for x, y in tx_struct['out']])
    total_in = sum([z for x, y, z in tx_struct['in']])
    tx_fees = total_in - total_out

    tx_struct['value'] = total_out
    tx_struct['fees'] = tx_fees
    return tx_struct

def get_raw_tx(tx_hash, rpc_connection):
    """
    Function that returns a raw transaction object by contacting JSON API run by 
    bitcoind daemon

    Parameters:
        tx_hash (str): hash of transaction to be parsed
        rpc_connection (RpcConnection object): object allowing for RPC calls to bitcoind daemon

    Returns:
        dict: dictionary containing raw transaction information 
    """

    try:
        return rpc_connection.getrawtransaction(tx_hash, True)
    except JSONRPCException:
        return None

def get_out_addrs(tx):
    """
    Function that returns a list of tuples from parsing the transaction output addresses. 
    Each tuple in list consists of the output wallet address along with the amount of 
    bitcoin sent to address as part of transaction

    Parameters:
        tx (dict): result of get_raw_tx function call

    Returns:
        list: a list of tuples where each tuple is of the form (wallet_address, amnt of bitcoin sent)
    """

    out_info = [(x['scriptPubKey']['addresses'], (int) (x['value'] * btc_unit)) 
        for x in tx['vout'] if 'addresses' in x['scriptPubKey']]
    out_addrs = [(x[0], y) for x, y in out_info if len(x) >= 1]
    return out_addrs

def get_in_addrs(tx, rpc_connection):
    """
    Function that returns a list of tuples from parsing the transaction input addresses. 
    Each tuple in list consists of the input wallet address along with the amount of 
    bitcoin sent to address as part of transaction as well as the transaction that is 
    being used to fund the input address.

    Parameters:
        tx (dict): result of get_raw_tx function call

    Returns:
        list: a list of tuples where each tuple is of the form (funding_tx, 
            wallet_address, amnt of bitcoin sent)
    """
    funding_txs = [(get_raw_tx(x['txid'], rpc_connection), x['vout'])for x in tx['vin']]
    lst = [(tx['hash'], get_out_addrs(tx)[out_inx]) for tx, out_inx in funding_txs]
    return [(x, y[0], y[1]) for x, y in lst]

def coalesce_input_addrs(tx_input):
    """
    Function takes as argument a list of input addresses for a specific transaction and groups
    them together based on the wallet address, aggregating the amount of money spent by each
    address in transaction.

    For example,  the input [("addr1", 10), ("addr2", 5), ("addr1", 5)] is grouped to
    {"addr1": 15, "addr2": 5}

    Parameters:
        tx_inputs (lst): list of tuples where each tuple consists of a wallet address
                        along with the amount of bitcoin sent (i.e. tx linking)
    
    Returns:
        dct: a dictionary similar to example described above
    """

    dct_tmp = {x: [b for a, b in tx_input if a is x] for x, y in tx_input}
    return {x: sum(y) for x, y in dct_tmp.items()}
