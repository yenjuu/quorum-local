import os
import json
import time
import pprint
import sqlite3
import secrets
import threading
from web3 import Web3
from web3.middleware import geth_poa_middleware
from web3.providers.eth_tester import EthereumTesterProvider

# link to quorum
quorum_url = "http://127.0.0.1:22003"


web3 = Web3(Web3.HTTPProvider(quorum_url))
web3.middleware_onion.inject(geth_poa_middleware, layer=0)
web3.eth.defaultAccount = web3.eth.accounts[0]
web3.parity.personal.unlock_account(web3.eth.accounts[0], "123", 15000)

gov_acct = web3.eth.accounts[0]


"""EO的代表：
- 2個listener: 聽最小參與物件數達標的事件、聽exchange_result
- 負責丟random number給白名單合約計算白名單
- 不負責matching
- 聽到交換結果出來後，要重啟一個 lis_setWhitelist
"""


def db_link():
    # link to DB
    db_url = r'/Users/ariel/quorum-local/sqlite/quorum.db'
    db_conn = sqlite3.connect(db_url)
    cur = db_conn.cursor()
    return (cur, db_conn)


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


def getObjAttr(tx_hash):
    # 根據註冊物件時的log tash，看此物件的屬性是什麼
    contract_interface = contract_instance("registered")
    tx_receipt = web3.eth.waitForTransactionReceipt(tx_hash)
    log_to_process = tx_receipt['logs'][0]
    processed_logs = contract_interface.events.logObjs().processLog(log_to_process)
    obj_attr = processed_logs['args']['attr']
    print(f"> Object attribute: {obj_attr} \n")
    print(f"> Get {obj_attr} contract_interface. \n")
    # 取得屬性合約 ABI, address
    contract_interface = contract_instance("attrRecord")
    attr_name, log_hash = contract_interface.functions.get_a_data(
        obj_attr).call({"gasLimit": 1000000000})
    if attr_name == "null":
        print(f"> '{obj_attr}' contract isn't exist. \n")
    else:
        # 有屬性合約 先從attrRecord合約裡抓log hash，去log查address跟abi，對屬性合約做交易
        print(
            f"> Get attr contract name: {attr_name}, Contract log hash: {log_hash }\n")
        tx_receipt = web3.eth.waitForTransactionReceipt(log_hash)
        log_to_process = tx_receipt['logs'][0]
        processed_logs = contract_interface.events.setLog().processLog(log_to_process)
        abi = processed_logs['args']['attrABI']
        address = processed_logs['args']['attrAddress']
        contract_interface = contract_interact(abi, address)
    return obj_attr, contract_interface


def randomNum():
    # 聽到參加者夠發的event gov就發隨機數到合約裡
    r = secrets.randbits(64)
    contract_interface = contract_instance("whitelist")
    print("> Calculate the difference of user's secrets with a random number. \n")
    contract_interface.functions.calc_random(
        r).transact({'from': gov_acct})
    # print(contract_interface.functions.get_data().call())
    print("!!!")
    contract_interface_2 = contract_instance("whitelist")
    contract_interface_2.functions.sort().transact({'from': gov_acct})
    print("???")
    # pprint.pprint(contract_interface.functions.get_difference().call({"gasLimit": 1000000000}))
    print("\n")


"""
設定白名單
"""


def set_whitelist():
    # 設置白名單，可更改要取所有隨機數中前 X% 的物品進入白名單，做交換。
    x = 10  # 隨著總人數不同 同樣％數 除的數字要不同
    print("> Setting whitelist...\n")
    contract_interface = contract_instance("whitelist")
    print(f"> Select the top {x} objects to add to the whitelist\n")
    tx_hash = contract_interface.functions.set_whiteList(
        x).transact({'from': gov_acct})
    tx_receipt = web3.eth.waitForTransactionReceipt(web3.toHex(tx_hash))
    log_to_process = tx_receipt['logs'][0]
    processed_logs = contract_interface.events.whitelist_log().processLog(log_to_process)
    print(">>>>>>>>>>>> Timestamp(白名單產生): ", time.time(), " <<<<<<<<<<<<")
    print("> Whitelist: ")
    whitelist = processed_logs['args']['whitelist']
    print(whitelist, "\n")

    return whitelist


"""
清理物件紀錄
"""


def clean(_hash_a, _hash_b):
    # TODO: 所有matching執行緒結束後，清空白名單
    # 刪除合約裡：whitelist secrect array裡已換完的 tx_hash, secret
    print("> Heard exchange success event, clean tx_hash and secrets on whitelist contract. \n")
    contract_interface = contract_instance("whitelist")
    contract_interface.functions.clean(
        str(_hash_a), str(_hash_b)).transact({'from': gov_acct})

    print("> Delete exchanged records on attribute contract. \n")
    objAttr, contract_interface = getObjAttr(_hash_a)
    contract_interface.functions.delete_data(
        _hash_a).transact({'from': gov_acct})
    objAttr, contract_interface = getObjAttr(_hash_b)
    contract_interface.functions.delete_data(
        _hash_b).transact({'from': gov_acct})
    print("> Exchange success objects' records are deleted. \n")
    # 再起一個whitelist listener
    lis_setWhitelist()


def clean_expired():
    # 清掉過期未交換成功的物件
    pass


def handle_event(event):
    pprint.pprint(web3.toJSON(event))
    print("handle event")
    randomNum()
    whitelist = set_whitelist()
    time.sleep(1)


def handle_event_result(event):
    pprint.pprint(web3.toJSON(event))
    print("> Got exchange success result event!\n")
    event_log = json.loads(json.dumps(eval(web3.toJSON(event))))
    hash_a = event_log['args']['hash_a']
    hash_b = event_log['args']['hash_b']
    clean(hash_a, hash_b)


def log_loop(event_filter, poll_interval):
    ident = threading.get_ident()
    tag = True
    while tag:
        for event in event_filter.get_new_entries():
            handle_event(event)
            print(f"lis_setWhitelist thread-{ident} .. \n")
            # time.sleep(poll_interval)
            tag = False
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


def lis_setWhitelist():
    contract_interface = contract_instance("whitelist")
    event_filter = contract_interface.events.participant.createFilter(
        fromBlock='latest')
    lis_setWhitelist = threading.Thread(
        target=log_loop, args=(event_filter, 5), daemon=True)
    lis_setWhitelist.start()
    print('> lis_setWhitelist listener start. \n')
    print(f'> lis_setWhitelist listener: {threading.get_ident()} \n')
    lis_setWhitelist.join()
    print("> lis_setWhitelist listener end. \n")


def main():
    contract_interface = contract_instance("whitelist")
    lis_setWhitelist()
    event_filter_result = contract_interface.events.exchange_result.createFilter(
        fromBlock='latest')
    lis_result = threading.Thread(target=log_loop_result, args=(
        event_filter_result, 5), daemon=True)
    lis_result.start()
    print("> Exchange result Listener start. \n")
    print(f"> lis_result listener: {threading.get_ident()} \n")

    # 呼叫clean function

    # 不應該聽到這隻監聽結束才對
    lis_result.join()
    print("> lis_result listener end. \n")


if __name__ == '__main__':
    main()
