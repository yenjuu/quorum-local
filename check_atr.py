#!/Users/ariel/quorum-local/venv/bin/python
import os
import sys
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
quorum_url = "http://127.0.0.1:22002"


web3 = Web3(Web3.HTTPProvider(quorum_url))
web3.middleware_onion.inject(geth_poa_middleware, layer=0)
web3.eth.defaultAccount = web3.eth.accounts[0]
web3.parity.personal.unlock_account(web3.eth.accounts[0], "123", 15000)


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


def check(wl_attr):
    
    gov_acct = web3.eth.accounts[0]
    print(f"> Check {wl_attr} attribute contract exist or not \n")
    # 從attrRecord contract裡查有無此屬性合約
    contract_interface = contract_instance("attrRecord")
    attr_name, log_hash = contract_interface.functions.get_a_data(
        wl_attr).call({"gasLimit": 1000000000})

    if attr_name == "null":
        print(attr_name)
        print(log_hash)
        print('this is null')
        return (False, False)
    else:    
        print(attr_name, log_hash)
        print('this is not null')
        return (attr_name, log_hash)


if __name__ == "__main__":
    print("Check attribute exist or not")
    wl_attr = input("Input attribute name: ")
    check(wl_attr)