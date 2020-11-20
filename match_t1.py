import os
import sys
import json
import time
import pprint
import sqlite3
import secrets
import pyautogui
import threading
from web3 import Web3
from web3.middleware import geth_poa_middleware
from web3.providers.eth_tester import EthereumTesterProvider
import check_atr

# link to quorum
quorum_url = "http://127.0.0.1:22003"


web3 = Web3(Web3.HTTPProvider(quorum_url))
web3.middleware_onion.inject(geth_poa_middleware, layer=0)
web3.eth.defaultAccount = web3.eth.accounts[0]
web3.parity.personal.unlock_account(web3.eth.accounts[0], "123", 15000)

gov_acct = web3.eth.accounts[0]


def db_link():
    # link to DB
    db_url = r'/Users/ariel/quorum-local/sqlite/quorum.db'
    db_conn = sqlite3.connect(db_url)
    cur = db_conn.cursor()
    return (cur, db_conn)


class Workers(threading.Thread):
    def __init__(self, num, tx_hash):
        threading.Thread.__init__(self)
        self.num = num
        self.tx_hash = tx_hash

    # def run(self):
    #     try:
    #         raise Exception('An error occured here.')
    #     except Exception:
    #         # 异常信息元祖放入队列传递给父进程
    #         self.bucket.put(sys.exc_info())

    def getWishlist(self, contract_interface):
        print("> Thread", (self.num+1))
        print("> tx_hash:", self.tx_hash, "\n")
        # 抓物件註冊log中的物件屬性、wishlist
        tx_receipt = web3.eth.waitForTransactionReceipt(self.tx_hash)
        log_to_process = tx_receipt['logs'][0]
        processed_logs = contract_interface.events.logObjs().processLog(log_to_process)
        obj_attr = processed_logs['args']['attr']
        wishlist = processed_logs['args']['wishlist'].split("/")
        print(f"> Object attribute(A): {obj_attr} \n")
        print(f"> Wishlist(A): {wishlist} \n")
        print(f"> First priority attr of wishlist(A): {wishlist[1]}\n")
        # 確認願望清單第一名屬性有無對應的屬性合約
        hash_a = self.tx_hash
        checkAttrRecord(obj_attr, wishlist[1], hash_a)
        # NOTE: 同個使用者不能換到自己的東西，好像還沒寫排除的條件
        time.sleep(0.5)


'''
與合約互動用的function
'''


def contract_instance(contract_name):
    # print(f"> Getting {contract_name} contract address... \n")
    cur, db_conn = db_link()
    cur.execute("SELECT abi, address FROM contract_data WHERE contract_name = ?", [
                contract_name])
    list = cur.fetchall()
    db_conn.close()
    abi = json.loads(json.dumps(eval(list[0][0])))
    address = list[0][1]
    # print(address + "\n")
    contract_interface = web3.eth.contract(
        address=address,
        abi=abi)
    return contract_interface


def contract_interact(abi, address):
    abi = json.loads(json.dumps(abi))
    contract_interface = web3.eth.contract(
        address=address,
        abi=abi)
    return contract_interface


'''
確認有無此屬性合約
'''


def checkAttrRecord(obj_attr, wl_attr, _hash_a):
    time.sleep(1)
    # obj_attr: A方的物件屬性; wl_attr: A方的 wishlist_attr_1
    print(f"> Check {wl_attr} attribute contract exist or not \n")
    # 從attrRecord contract裡查有無此屬性合約
    # result, attr_name, log_hash = check_atr.check(wl_attr)
    contract_interface = contract_instance("attrRecord")
    attr_name, log_hash = contract_interface.functions.get_a_data(
        wl_attr).call({"gasLimit": 1000000000})
    # print("!!!!!!!", attr_name, log_hash)
    
    if attr_name == "null":
        print(f"> '{wl_attr}' contract isn't exist. \n")
        print(">>>>>>>>>>>> Timestamp(交換失敗): ", time.time(), " <<<<<<<<<<<<")
    # if result == False:
    #     print(f"> '{wl_attr}' contract isn't exist. \n")
    #     print(">>>>>>>>>>>> Timestamp(交換失敗): ", time.time(), " <<<<<<<<<<<<")

    else:
        # 有屬性合約 先從attrRecord合約裡抓log hash，去log查address跟abi，對屬性合約做交易
        print(
            f"> Get attr contract name: {attr_name}, Contract log hash: {log_hash }\n")
        tx_receipt = web3.eth.waitForTransactionReceipt(log_hash)
        time.sleep(1)
        log_to_process = tx_receipt['logs'][0]
        processed_logs = contract_interface.events.setLog().processLog(log_to_process)
        abi = processed_logs['args']['attrABI']
        address = processed_logs['args']['attrAddress']
        contract_interface = contract_interact(abi, address)
        # 從此屬性合約中，抓出每一筆紀錄
        records = contract_interface.functions.get_data().call(
            {"gasLimit": 1000000000})
        pprint.pprint(records)
        print(f"> Get all records on '{wl_attr}' contract.\n")
        # NOTE:依序看wishlist有無符合的物品可換？？
        getAttrRecord(records, wl_attr, obj_attr, _hash_a)


'''
比對屬性合約上的物件
'''


def getAttrRecord(records, attr, obj_attr, _hash_a):
    record = records[0].split(";")
    record.pop()
    print(f"> {attr} contract: {len(record)} records. \n")
    for i in range(len(record)):
        # detail: 存在屬性合約(B)的 user account, hash_b, timestamp
        detail = record[i].split("/")
        print(f"> Check {attr} contract record No.{i+1} \n")
        # 依序確認在屬性合約上的每條紀錄有無想要Ａ的物品
        hash_b = detail[1]
        wishlist_1 = getObjLog(hash_b)
        # 確認是否交換成功
        if wishlist_1 == obj_attr:
            # 交換成功丟雙方hash到log
            print(">>> Exchange success <<<\n")
            print(">>>>>>>>>>>> Timestamp(交換成功): ", time.time(), " <<<<<<<<<<<<")
            contract_interface = contract_instance("whitelist")
            contract_interface.functions.set_result(
                str(_hash_a), str(hash_b)).transact({'from': gov_acct})
            break
        else:
            print(
                f"> User (A): have {obj_attr}. User (B): want {wishlist_1}. \n")
            if (i+1) == len(record):
                print(f"No records in {attr} contract anymore. \n")
                print(f">>> Exchange failed <<< \n")
            else:
                print(f"> Record {i+1} exchange failed. Check next record. \n")


'''
取party A物件的願望清單
'''


def getObjLog(tx_hash):
    # 根據註冊物件時的log tash，看此物件的願望清單排序1是什麼
    contract_interface = contract_instance("registered")
    tx_receipt = web3.eth.waitForTransactionReceipt(tx_hash)
    log_to_process = tx_receipt['logs'][0]
    processed_logs = contract_interface.events.logObjs().processLog(log_to_process)
    # print(processed_logs['args'])
    wishlist = processed_logs['args']['wishlist'].split("/")
    #print(f"> Wishlist: {wishlist}\n")
    print(f"> First priority attr of wishlist: {wishlist[1]} \n")
    return wishlist[1]


def randomNum():
    # 聽到參加者夠發的event gov就發隨機數到合約裡
    r = secrets.randbits(64)
    contract_interface = contract_instance("whitelist")
    print("> Calculate the difference of user's secrets with a random number. \n")
    t_hash = contract_interface.functions.calc_random(
        r).transact({'from': gov_acct})
    web3.eth.waitForTransactionReceipt(t_hash)
    # print(contract_interface.functions.get_data().call())
    t_hash = contract_interface.functions.sort().transact({'from': gov_acct})
    web3.eth.waitForTransactionReceipt(t_hash)
    # pprint.pprint(contract_interface.functions.get_difference().call({"gasLimit": 1000000000}))
    print("\n")


def set_whitelist():
    # 設置白名單，可更改要取所有隨機數中前 X% 的物品進入白名單，做交換。
    x = 2  # 隨著總人數不同 同樣％數 除的數字要不同
    print("> Setting whitelist...\n")
    contract_interface = contract_instance("whitelist")
    print(f"> Select the top {x} objects to add to the whitelist\n")
    tx_hash = contract_interface.functions.whiteList(
        x).transact({'from': gov_acct})
    tx_receipt = web3.eth.waitForTransactionReceipt(web3.toHex(tx_hash))
    log_to_process = tx_receipt['logs'][0]
    processed_logs = contract_interface.events.whitelist_log().processLog(log_to_process)
    print("> Whitelist: ")
    whitelist = processed_logs['args']['whitelist']
    print(whitelist, "\n")

    return whitelist


def match(whitelist):
    print("> Start", len(whitelist), " threading..\n")
    # 建立與白名單相同數量的執行緒
    contract_interface = contract_instance("registered")
    worker = []
    for i in range(len(whitelist)):
        time.sleep(0.1)
        worker.append(Workers(i, whitelist[i]))
        worker[i].getWishlist(contract_interface)
        worker[i].start()

    # # 循環獲取子線程的異常訊息
    # while 1:
    #     try:
    #         exc = bucket.get(block=False)
    #     except worker.length == 0:
    #         pass
    #     else:
    #         exc = exc_obj, exc_trace = exc
    #         # deal with the exception
    #         print(exc_type, exc_obj)
    #         print(exc_trace)

    # for i in range(len(worker)):
    #     worker[i].join()
    #     if worker[i].isAlive():
    #         continue
    #     else:
    #         print(f"> worker{i} done.")
    #         break


def clean():
    # TODO: 所有matching執行緒結束後，清空白名單
    # 刪除合約裡：whitelist secrect array裡已換完的 tx_hash, secret
    # 再起一個whitelist listener

    # 清理過期物件（要做？或分另個func做）
    pass


def get_event_log(event_hash):
    contract_interface = contract_instance('whitelist')
    tx_receipt = web3.eth.waitForTransactionReceipt(event_hash)
    log_to_process = tx_receipt['logs'][0]
    processed_logs = contract_interface.event.whitelist_log().processLog(log_to_process)
    print("> whitelist: ")
    whitelist = processed_logs['args']['whitelist']
    print(whitelist, "\n")
    return whitelist


def handle_event(event):
    pprint.pprint(web3.toJSON(event))
    event_log = json.loads(json.dumps(eval(web3.toJSON(event))))
    whitelist = event_log['args']['whitelist']
    time.sleep(1)
    match(whitelist)


def handle_event_result(event):
    pprint.pprint(web3.toJSON(event))
    print("> Got exchange success result event!\n")
    # TODO: 清掉屬性合約裡對應的 tx_hash（clean func）


def log_loop(event_filter, poll_interval):
    ident = threading.get_ident()
    tag = True
    while tag:
        for event in event_filter.get_new_entries():
            handle_event(event)
            print(f"lis_whitelist thread-{ident} .. \n")
            # time.sleep(poll_interval)
            #tag = False
            break


def log_loop_result(event_filter_result, poll_interval):
    # 聽交換結果的listener要一直跑
    ident = threading.get_ident()
    tag = True
    while tag:
        for event in event_filter_result.get_new_entries():
            handle_event_result(event)
            print(f"lis_result thread={ident}.. \n")
            #tag = False
            break


def main():
    contract_interface = contract_instance("whitelist")
    event_filter = contract_interface.events.whitelist_log.createFilter(
        fromBlock='latest')
    lis_whitelist = threading.Thread(
        target=log_loop, args=(event_filter, 5), daemon=True)
    lis_whitelist.start()
    print('> lis_whitelist listener start. \n')
    print(f'> lis_whitelist listener: {threading.get_ident()} \n')

    # TODO: 聽到交換成功event，清掉屬性合約裡對應的 tx_hash
    event_filter_result = contract_interface.events.exchange_result.createFilter(
        fromBlock='latest')
    lis_result = threading.Thread(target=log_loop_result, args=(
        event_filter_result, 5), daemon=True)
    lis_result.start()
    print("> Exchange result Listener start. \n")
    print(f"> lis_result listener: {threading.get_ident()} \n")

    lis_whitelist.join()
    print("> lis_whitelist listener end. \n")
    # 呼叫clean function

    # 不應該聽到這隻監聽結束才對
    lis_result.join()
    print("> lis_result listener end. \n")


if __name__ == '__main__':
    main()
