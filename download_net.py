from models.BtcModels import BtcAddress, BtcTransaction, TxInputAddrInfo, TxOutputAddrInfo, get_credentials
from python_algorithms.basic.union_find import UF
from datetime import datetime
import argparse
import pickle
import sys
import traceback
import logging
import logging.handlers
import smtplib

def check_otc_conditions(output_tx, change_addr_id):
    # transaction cannot be a coinbase transaction
    if output_tx.coinbase_tx:
        return False

    tx_input_addrs = set([x.address for x in output_tx.input_addrs])
    tx_output_addrs = set([x.address for x in output_tx.output_addrs])

    # there cannot exist a self-change address (i.e an input address
    # also shows up in the output)
    if tx_input_addrs.intersection(tx_output_addrs):
        return False
    
    # all other output address have been seen before
    for addr in output_tx.output_addrs:
        if addr.addr_ref_id == change_addr_id:
            continue
        
        addr_links_input = AddressTransactionLink.objects(addr_ref_id=addr.addr_ref_id, 
            addr_used_as_input=True).count()
        addr_links_output = AddressTransactionLink.objects(addr_ref_id=addr.addr_ref_id, 
            addr_used_as_input=False).count()

        if addr_links_input == 0 and addr_links_output <= 1:
            return False

    return True

def send_email_notif(subject, body):
    server = smtplib.SMTP('smtp.gmail.com', 587)

    # set up HELO
    server.connect("smtp.gmail.com", 587)
    server.ehlo()
    server.starttls()
    server.ehlo()

    # get credentials
    credentials_dct = get_credentials('credentials/test_user_credentials')

    # login to server
    server.login(credentials_dct['username'], credentials_dct['password'])

    # Construct message with subject and body. Send message
    # to listed recipient
    FROM = credentials_dct['email']
    TO = credentials_dct['recipient']
    message = """From: %s\nTo: %s\nSubject: %s\n\n%s
    """ % (FROM, TO, subject, body)
    server.sendmail(FROM, TO, message)

def get_cc():
    try:
        '''addrs = {}

        num_addrs = BtcAddress.objects().count()
        batch_size = 10000
        batch_start = 0
        
        print("querying all addresses")
        while batch_start < num_addrs - 1:
            batch_end = batch_start + batch_size
            print("processing addrs up to id: ", batch_end)

            batch_addrs = BtcAddress.objects(ref_id__lte=batch_end, 
                ref_id__gte=batch_start).only('ref_id', 'neighbor_addrs').all()
            print("batch received going to add to dict...")

            for addr in batch_addrs:
                addrs[addr.ref_id] = addr

            print("finished adding batch to dict...")
            
            batch_start += batch_size'''

        num_nodes = max(addrs.keys()) + 1
        print("number of nodes: ", num_nodes)

        union_find = UF(num_nodes)

        print("identifying nodes...")
        possible_otc_addrs = []

        for identifer, addr_obj in addrs.items():
            neighbor_addrs = addr_obj.neighbor_addrs
            if len(neighbor_addrs) != 0:
                for reference in neighbor_addrs:
                    union_find.union(reference, identifer)
            else:
                possible_otc_addrs.append(identifer)
        print("=====union find done=====")

        uf_dict = {x: union_find.find(x) for x in addrs.keys()}

        for addr_ref_id in possible_otc_addrs:
            num_txs_using_addr_as_input = AddressTransactionLink.objects(addr_ref_id=addr_ref_id, 
                addr_used_as_input=True).count()
            num_txs_using_addr_as_output = AddressTransactionLink.objects(addr_ref_id=addr_ref_id, 
                addr_used_as_input=False).count()
        
            if num_txs_using_addr_as_input == 0 and num_txs_using_addr_as_output == 1:
                output_tx_link = AddressTransactionLink.objects(addr_ref_id=addr_ref_id, 
                    addr_used_as_input=False).only('tx_ref_id').first()
                output_tx = BtcTransaction.objects(ref_id=output_tx_link.tx_ref_id).first()
                otc_addr = check_otc_conditions(output_tx, addr_ref_id)
                if otc_addr:
                    input_addr = output_tx.input_addrs[0].addr_ref_id
                    node_id = uf_dict[input_addr]
                    uf_dict[addr_ref_id] = node_id

        with open("pickles/cc.pickle", "wb") as f:
            pickle.dump(uf_dict, f)
        
        send_email_notif("Address Clustering Finished", "The address clustering script has finished")

        return uf_dict
    except Exception as e:
        print("Exception occured while clustering data")
        body = """
        Please check the download_net.py script\n
        he following exception has occured: %s
        """ % (str(e))
        send_email_notif("Error Occured", body)
        traceback.print_exc()
        sys.exit(1)

def get_cc_for_addrs(addr_ids):
    addr_ids_list = list(addr_ids)
    
    # retrieve all addresses necessary for transactions
    # that yet to be clustered
    print("retrieving nodes in transaction...")
    addrs = {x.ref_id: x for x in BtcAddress.objects(
            ref_id__in=addr_ids_list).only('ref_id', 'neighbor_addrs').all()}
    print("done retrieving nodes...")

    # normalize address ids to set of [0, num_addrs]
    addrs_to_normalized_addrs = {}
    start_inx = 0
    sorted_keys = sorted(addrs.keys())
    for key in sorted_keys:
        addrs_to_normalized_addrs[key] = start_inx
        start_inx += 1

    num_addrs = len(addr_ids_list)
    print("number of nodes: ", num_addrs)
    union_find = UF(num_addrs)

    print("identifying nodes...")
    possible_otc_addrs = []

    for identifer, addr_obj in addrs.items():
        identifer_node_id = addrs_to_normalized_addrs[identifer]
        neighbor_addrs = addr_obj.neighbor_addrs
        if len(neighbor_addrs) != 0:
            for reference in neighbor_addrs:
                if reference in addrs_to_normalized_addrs:
                    ref_node_id = addrs_to_normalized_addrs[reference]
                    union_find.union(ref_node_id, identifer_node_id)
        else:
            possible_otc_addrs.append(identifer)
    print("=====union find done=====")

    # {addr_ref_id: node_id}
    uf_dict = {x: union_find.find(addrs_to_normalized_addrs[x]) for x in addrs.keys()}

    # TODO: change addresses

    return uf_dict

def create_graph_file(graph_file, start_time=0, end_time=0, use_pickle=False):
    try:
        print("graph file: ", graph_file)

        '''print("====getting connected components====")
        if use_pickle:
            with open("pickles/cc.pickle", "rb") as f:
                cc_dict = pickle.load(f)
        else:
            cc_dict = get_cc()
        print("====finished getting CC====")

        valid_ref_ids = set(cc_dict.keys())'''
        print("getting all transactions in time window...")
        time_hint = [('_cls', 1), ('time', 1)]
        if start_time == 0 and end_time == 0:
            txs = BtcTransaction.objects(coinbase_tx=False)
        elif end_time == 0:
            txs = BtcTransaction.objects(coinbase_tx=False, time__gte=start_time).hint(time_hint)
        else:
            txs = BtcTransaction.objects(coinbase_tx=False, time__gte=start_time, 
                time__lte=end_time).hint(time_hint)

        addresses = set()
        for tx in txs:
            tx_addrs = [x.addr_ref_id for x in tx.input_addrs] + [x.addr_ref_id for x in tx.output_addrs]
            for addr in tx_addrs:
                addresses.add(addr)
        cc_dict = get_cc_for_addrs(addresses)
        valid_ref_ids = set(cc_dict.keys())

        with open(graph_file, "w") as f:
            for tx in txs.all():
                ref_ids_set_input = set([x.addr_ref_id for x in tx.input_addrs])
                ref_ids_set_output = set([x.addr_ref_id for x in tx.output_addrs])

                if ((ref_ids_set_input - valid_ref_ids)) or \
                    ((ref_ids_set_output - valid_ref_ids)):
                    continue

                input_node_wealth = sum([x.wealth for x in tx.input_addrs])
                dct_tmp = {x.addr_ref_id: x for x in tx.input_addrs}
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
        body_msg = "Transactions have been saved as graph format in %s file" % (graph_file)
        send_email_notif("Download Finished", body_msg)
    except Exception as e:
        print("Exception occured while creating graph format")
        body = """
        Please check the download_net.py script\n
        he following exception has occured: %s
        """ % (str(e))
        # send_email_notif("Error Occured", body)
        traceback.print_exc()
        sys.exit(1)


def documentation():
    print("<input_node_id>,<input_node_creation_time>, \
        <input_node_wealth_at_tx>,<tx_value>,<tx_time>,<tx_inx> \
        <output_node_id>,<output_node_creation_time>,<output_node_wealth_at_tx>")

def find_time_window():
    min_time = BtcAddress.objects.order_by("+ref_id").limit(-1).first().time
    max_time = BtcAddress.objects.order_by("-ref_id").limit(-1).first().time
    print("Min Time: ", datetime.utcfromtimestamp(min_time).strftime('%Y-%m-%d %H:%M:%S'))
    print("Max Time: ", datetime.utcfromtimestamp(max_time).strftime('%Y-%m-%d %H:%M:%S'))

def get_time_stamp(time_string):
    dt = datetime.strptime(time_string, "%Y-%m-%d")
    return (int) (dt.timestamp())

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Download blockchain data as graph')
    parser.add_argument('-t', '--times', action='store_true')
    parser.add_argument('-d', '--download', action='store_true')
    parser.add_argument('--schema', action='store_true')
    parser.add_argument('-c', '--cached', action='store_true')
    parser.add_argument('-s', '--store_cc', action='store_true')
    parser.add_argument('--test_email', action='store_true')
    parser.add_argument('integers', 
        nargs='*', help='an integer in the range of min_time to max_time')
    args = parser.parse_args()

    if args.schema:
        documentation()

    if args.times:
        find_time_window()
    
    if args.store_cc:
        get_cc()
    
    if args.test_email:
        send_email_notif("TEST EMAIL", "this is a test email!\nHope it works :)")

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
            time_stamp = get_time_stamp(times[0])
            create_graph_file(times[1], start_time=time_stamp, use_pickle=args.cached)
        elif (len(times) == 3):
            start_time_stamp = get_time_stamp(times[0])
            end_time_stamp = get_time_stamp(times[1])
            create_graph_file(times[2], start_time=start_time_stamp, 
                end_time=end_time_stamp, use_pickle=args.cached)
