from models.BtcModels import BtcAddress, BtcTransaction, TxInputAddrInfo, TxOutputAddrInfo
from python_algorithms.basic.union_find import UF
import pickle
import sys

def get_cc():
    addrs = {x.ref_id: x for x in BtcAddress.
        objects.only('ref_id', 'neighbor_addrs', 'time').all()}
    
    pass

def create_graph_file(start_time, end_time):
    cc_dict = get_cc()

    for tx in BtcTransaction.objects(time__gte=start_time, time__lte=end_time, hint='time'):
        pass

if __name__ == "__main__":
    start_time = int(sys.argv[1])
    end_time = int(sys.argv[2])
    create_graph_file(start_time, end_time)