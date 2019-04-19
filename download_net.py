from models.BtcModels import BtcAddress, BtcTransaction, TxInputAddrInfo, TxOutputAddrInfo
from python_algorithms.basic.union_find import UF
import pickle
import sys

def get_cc():
    addrs = {x.ref_id: x for x in BtcAddress.
        objects.only('ref_id', 'neighbor_addrs', 'time').all()}

    print("Min Time: ", min([x.time for x in addrs.values()]))
    print("Max Time: ", max([x.time for x in addrs.values()]))

    num_nodes = max(addrs.keys()) + 1
    union_find = UF(num_nodes)

    print("identifying nodes...")
    for identifer, addr_obj in addrs.items():
        neighbor_addrs = addr_obj.neighbor_addrs
        for reference in neighbor_addrs:
            union_find.union(reference, identifer)
    print("=====union find done=====")

    uf_dict = {x: union_find.find(x) for x in addrs.keys()}

    with open("pickles/cc.pickle", "wb") as f:
        pickle.dump(uf_dict, handle)

def create_graph_file(start_time, end_time):
    cc_dict = get_cc()

    for tx in BtcTransaction.objects(time__gte=start_time, time__lte=end_time, hint='time'):
        pass

if __name__ == "__main__":
    #start_time = int(sys.argv[1])
    #end_time = int(sys.argv[2])
    #create_graph_file(start_time, end_time)
    # addr_objs = BtcAddress.objects.only('time').all()
    # print("Min Time: ", min([x.time for x in addr_objs]))
    # print("Max Time: ", max([x.time for x in addr_objs]))
    get_cc()
