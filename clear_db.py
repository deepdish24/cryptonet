from models.BtcModels import BtcAddress, BtcTransaction, TxInputAddrInfo, TxOutputAddrInfo

def clear_db():
    BtcAddress.drop_collection()
    BtcTransaction.drop_collection()

if __name__ == "__main__":
    clear_db()
    '''tx_hash = "8f1f7c3c476c102781aa06bd162d21d546cf14a259c40336ea58a6c28a853941"
    tx = BtcTransaction.objects(hash=tx_hash).first()
    for in_addr in tx.input_addrs:
        print(in_addr.address)
        print(in_addr.value)
    print(len(tx.output_addrs))'''

    '''address = "1GDAjtGDgfbB7QXXfmvBAgRZtzkgaJbaoE"
    addr_obj = BtcAddress.objects(addr=address).first()
    print(addr_obj.neighbor_addrs)
    print(addr_obj.used_as_input)'''