from models.BtcModels import BtcAddress, BtcTransaction, TxInputAddrInfo, TxOutputAddrInfo
from python_algorithms.basic.union_find import UF
import argparse
import pickle
import sys

def get_cc(change_addr_clustering=False):
    addrs = {x.ref_id: x for x in BtcAddress.
        objects.only('ref_id', 'neighbor_addrs', 'time').all()}

    # txs = BtcTransaction.objects.all()

    num_nodes = max(addrs.keys()) + 1
    print("number of nodes: ", num_nodes)

    union_find = UF(num_nodes)

    print("identifying nodes...")
    for identifer, addr_obj in addrs.items():
        neighbor_addrs = addr_obj.neighbor_addrs
        for reference in neighbor_addrs:
            union_find.union(reference, identifer)
    print("=====union find done=====")

    uf_dict = {x: union_find.find(x) for x in addrs.keys()}

    with open("pickles/cc.pickle", "wb") as f:
        pickle.dump(uf_dict, f)
    
    return uf_dict

def create_graph_file(graph_file, start_time=0, end_time=0, use_pickle=False):
    print("graph file: ", graph_file)

    print("====getting connected components====")
    if use_pickle:
        with open("pickles/cc.pickle", "rb") as f:
            cc_dict = pickle.load(f)
    else:
        cc_dict = get_cc()
    print("====finished getting CC====")

    valid_ref_ids = set(cc_dict.keys())

    if start_time == 0 and end_time == 0:
        txs = BtcTransaction.objects(coinbase_tx=False)
    elif end_time == 0:
        txs = BtcTransaction.objects(coinbase_tx=False, time__gte=start_time).hint('time')
    else:
        txs = BtcTransaction.objects(coinbase_tx=False, time__gte=start_time, time__lte=end_time).hint('time')
    
    with open(graph_file, "w") as f:
        for tx in txs.all():
            ref_ids_set_input = set([x.addr_ref_id for x in tx.input_addrs])
            ref_ids_set_output = set([x.addr_ref_id for x in tx.output_addrs])

            if ((ref_ids_set_input - valid_ref_ids)) or \
                ((ref_ids_set_output - valid_ref_ids)):
                continue

            input_node_wealth = sum([x.wealth for x in tx.input_addrs])
            dct_tmp = {x.addr_ref_id: x for x in tx.input_addrs}
            # print(tx.hash, tx.coinbase_tx)
            input_node_creation_time = dct_tmp[min(dct_tmp)].address.fetch().time
            output_addr_objs_creation_times = {x.address: x.address.fetch().time for x in tx.output_addrs}

            
            input_cc_id = cc_dict[ref_ids_set_input.pop()]

            for output_addr in tx.output_addrs:
                output_node_creation_time = output_addr_objs_creation_times[output_addr.address]
                output_node_wealth = output_addr.wealth
                output_cc_id = cc_dict[output_addr.addr_ref_id]
                line = str(input_cc_id) + "," + str(input_node_creation_time) + "," + \
                    str(input_node_wealth) + "," + str(tx.tx_val) + "," + str(tx.time) + \
                        "," + str(tx.ref_id) + "," + str(output_cc_id) + "," + \
                            str(output_node_creation_time) + "," + str(output_node_wealth)
                f.write(line + "\n")


def documentation():
    print("<input_node_id>,<input_node_creation_time>, \
        <input_node_wealth_at_tx>,<tx_value>,<tx_time>,<tx_inx> \
        <output_node_id>,<output_node_creation_time>,<output_node_wealth_at_tx>")

def find_time_window():
    min_time = BtcAddress.objects.order_by("+ref_id").limit(-1).first()
    max_time = BtcAddress.objects.order_by("-ref_id").limit(-1).first()
    print("Min Time: ", min_time.time)
    print("Max Time: ", max_time.time)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Download blockchain data as graph')
    parser.add_argument('-t', '--times', action='store_true')
    parser.add_argument('-d', '--download', action='store_true')
    parser.add_argument('--schema', action='store_true')
    parser.add_argument('-c', '--cached', action='store_true')
    parser.add_argument('-s', '--store_cc', action='store_true')
    parser.add_argument('--change_clustering', action='store_true')
    parser.add_argument('integers', 
        nargs='*', help='an integer in the range of min_time to max_time')
    args = parser.parse_args()

    if args.schema:
        documentation()

    if args.times:
        find_time_window()
    
    if args.store_cc:
        get_cc(change_addr_clustering=args.change_clustering)

    if args.download:
        times = args.integers
        if (len(times) > 3):
            print("Error: more than 2 arguments passed in")
            sys.exit(1)
        
        if (len(times) == 0):
            print("Error: need to pass in filename for storing graph")
            sys.exit(1)
        elif (len(times) == 1):
            create_graph_file(times[0], use_pickle=args.cached)
        elif (len(times) == 2):
            create_graph_file(times[1], start_time=int(times[0]), use_pickle=args.cached)
        elif (len(times) == 3):
            create_graph_file(times[2], start_time=int(times[0]), 
                end_time=int(times[1]), use_pickle=args.cached)
