from models.BtcModels import BtcAddress, BtcTransaction, TxInputAddrInfo, TxOutputAddrInfo

def clear_db():
    BtcAddress.drop_collection()
    BtcTransaction.drop_collection()

if __name__ == "__main__":
    clear_db()
