import os
import json
import time
import pprint
import requests
import sqlite3
import secrets
import asyncio
from threading import Thread
from web3 import Web3
from web3.providers.eth_tester import EthereumTesterProvider
from web3.middleware import geth_poa_middleware


# link to quorum
quorum_url = ""
gov_acct = "0xf9231a78a826Efc09AeBC9ee2DaE826CC45aC583"
user_acct = ""
# quorum_url = "http://192.168.66.28:22000"
# quorum_url = "http://127.0.0.1:22000"

# web3 = Web3(Web3.HTTPProvider(quorum_url))
# #web3.middleware_onion.inject(geth_poa_middleware, layer=0)
# web3.eth.defaultAccount = web3.eth.accounts[0]
#web3.parity.personal.unlock_account(web3.eth.accounts[0], "123", 15000)


def db_link():
    # link to DB
    db_url = r'/home/quorum/quorum_code/sqlite/quorum.db'
    db_conn = sqlite3.connect(db_url)
    cur = db_conn.cursor()
    return (cur, db_conn)


def compile_contract(contract_source_file, contract_name=None):
    print(f'> Compiling {contract_source_file} \n')
    # os.system(f"solc --bin {contract_source_file} > bin/{contract_name}.bin")
    # os.system(f"solc --abi {contract_source_file} > bin/{contract_name}.abi")
    os.system(
        f"solc --combined-json abi,bin {contract_source_file} > bin/{contract_name}.json")

    compiled_file_path = f"{contract_source_file}:{contract_name}"

    with open(f"bin/{contract_name}.json")as json_file:
        compiled_sol = json.load(json_file)
        abi = compiled_sol['contracts'][compiled_file_path]['abi']
        bytecode = compiled_sol['contracts'][compiled_file_path]['bin']

    return abi, bytecode


def deploy_contract(acct, abi, bytecode, contract_name):
    print(f'> Deploying {contract_name} contract.. \n')
    abi = json.loads(abi)
    contract_interface = web3.eth.contract(abi=abi, bytecode=bytecode)
    tx_hash = contract_interface.constructor().transact()
    tx_receipt = web3.eth.waitForTransactionReceipt(tx_hash)
    contract = web3.eth.contract(
        address=tx_receipt.contractAddress,
        abi=abi
    )

    address = str(contract.address)
    abi = str(contract.abi)
    print(f"> Was {contract_name} contract deploy successful? ")
    pprint.pprint(tx_receipt['status'])
    print("> BlockNumber: ")
    pprint.pprint(tx_receipt['blockNumber'])
    print(f"> {contract_name} contract address: \n" + contract.address)

    return contract_name, address, abi


def saveToDB(contract_name, address, abi):
    cur, db_conn = db_link()
    # save contract data into DB
    cur.execute(
        "insert into contract_data(contract_name, abi, address) values (?, ?, ?)", (contract_name, abi, address))
    db_conn.commit()
    db_conn.close()


def contract_instance(contract_name):
    cur, db_conn = db_link()
    print(f"> Getting {contract_name} contract address... \n")
    cur.execute("SELECT abi, address FROM contract_data WHERE contract_name = ?", [
                contract_name])
    list = cur.fetchall()
    db_conn.close()
    abi = json.loads(json.dumps(eval(list[0][0])))
    address = list[0][1]
    print(address + "\n")
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


def registered(_acct, _obj, _attr, _wishlist):
    print("> Object is registering...")
    user_acct = _acct
    obj = _obj
    attr = _attr
    wishlist = _wishlist.split(",")
    wishlist = '/'.join(wishlist)
    contract_name = "registered"
    contract_interface = contract_instance(contract_name)
    print(f"> Send object data to {contract_name} contract...\n")
    tx_hash = contract_interface.functions.setUser(
        user_acct, obj, attr, wishlist).transact({'from': user_acct})
    print("> Transaction Hash: \n" + web3.toHex(tx_hash) + "\n")
    tx_receipt = web3.eth.waitForTransactionReceipt(web3.toHex(tx_hash))
    print("==== Object registered successful!==== \n")
    print(contract_interface.functions.getUser().call())
    user_acct = contract_interface.functions.getUser().call()[0]
    tx_hash = web3.toHex(tx_hash)
    attr = contract_interface.functions.getUser().call()[2]
    print("> Object attr: " + attr + "\n")
    return user_acct, tx_hash, attr


def saveHashToAttrContract(user_acct, tx_hash, attr):
    print(f"> Check {attr} attribute contract exist or not \n")
    # 從attrRecord contract裡查有無此屬性合約
    contract_interface = contract_instance("attrRecord")
    attrName, attrHash = contract_interface.functions.get_a_data(attr).call()
    #print(attrName, attrHash)
    # 無此屬性合約，要改模板，compile & deploy新的屬性合約，將產生屬性合約的hash記在attrRecord上，將user的tx hash記載屬性合約上
    if attrName == "null":
        print(f"> {attr} attribute contract is not exist. Start creating... \n")
        if os.path.isfile(f"bin/{attr}.json"):
            os.system(f"rm bin/{attr}.json")
            print(f"Old {attr} json file is deleted. \n")
        # 改模板
        fin = open("attr.txt", "rt")
        fout = open(f"contract/{attr}.sol", "wt")
        for line in fin:
            fout.write(line.replace("contract_name", attr))
        fin.close()
        fout.close()
        # 確認模板改好，成功產生solidity檔
        contract_source_file = f"contract/{attr}.sol"
        contract_name = str(attr)
        if os.path.isfile(contract_source_file):
            print(
                f"> {contract_source_file} solidity file is successfully created. \n")
            print(
                f"> Start compile and deploy {contract_name} attribute contract.... \n")
            abi, bytecode = compile_contract(
                contract_source_file, contract_name)
            attr_name, address, attr_abi = deploy_contract(
                gov_acct, abi, bytecode, contract_name)
            # 將屬性合約的address, abi 記錄到log裡，並將屬性合約名稱與部署的hash存到 attrRecord contract裡
            contract_interface = contract_instance("attrRecord")
            log_hash = contract_interface.functions.add_event(
                abi, address).transact({'from': user_acct})
            contract_interface.functions.add_data(
                attr_name, web3.toHex(log_hash)).transact({'from': user_acct})
            print("List attribute contracts in attrRecord.. \n")
            print(contract_interface.functions.get_all_data().call())
    # 有屬性合約 先從attrRecord合約裡抓log hash，去log查address跟abi，對屬性合約做交易
    attr_name, log_hash = contract_interface.functions.get_a_data(attr).call()
    print(f"Get attr name: {attr_name}, Log hash: {log_hash }\n")
    tx_receipt = web3.eth.waitForTransactionReceipt(log_hash)
    log_to_process = tx_receipt['logs'][0]
    processed_logs = contract_interface.events.setLog().processLog(log_to_process)
    abi = processed_logs['args']['attrABI']
    address = processed_logs['args']['attrAddress']
    contract_interface = contract_interact(abi, address)
    # 抓到屬性合約，將user tx hash記錄到屬性合約上
    timestamp = str(time.time())
    tx_receipt = web3.eth.waitForTransactionReceipt(web3.toHex(contract_interface.functions.add_data(
        user_acct, tx_hash, timestamp).transact({'from': user_acct})))
    log_to_process = tx_receipt['logs'][0]
    processed_logs = contract_interface.events.logObjs().processLog(log_to_process)
    print(processed_logs['args'])


def setWhitelist(tx_hash):
    s = secrets.randbits(64)
    print(f"\nGenerate user secret: {s} \n")
    contract_interface = contract_instance("whitelist")
    t_hash = contract_interface.functions.add_user_secret(
        tx_hash, s).transact({'from': user_acct})
    print("Add user secret to whitelist contract: " + web3.toHex(t_hash) + "\n")

    return s


def get_url(_url):
    global quorum_url
    quorum_url = _url
    global web3
    web3 = Web3(Web3.HTTPProvider(quorum_url))
    web3.middleware_onion.inject(geth_poa_middleware, layer=0)
    web3.eth.defaultAccount = web3.eth.accounts[0]
    web3.parity.personal.unlock_account(web3.eth.accounts[0], "123", 15000)


def run(_acct, _obj, _attr, _wishlist):
    global user_acct
    user_acct = _acct
    obj = _obj
    attr = _attr
    wishlist = _wishlist

    user_acct, tx_hash, attr = registered(user_acct, obj, attr, wishlist)
    saveHashToAttrContract(user_acct, tx_hash, attr)
    setWhitelist(tx_hash)
