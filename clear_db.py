from models.BtcModels import BtcAddress, BtcTransaction, TxInputAddrInfo, TxOutputAddrInfo
from models.models import AddressTransactionLink

def clear_db():
    BtcAddress.drop_collection()
    BtcTransaction.drop_collection()
    AddressTransactionLink.drop_collection()

if __name__ == "__main__":
    clear_db()