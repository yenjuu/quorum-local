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
import register

"""
測試用，一次上架多個物件到區塊鏈上
"""

env_num = 3
total_num = 13


def match(file_name):
    for i in range(env_num+1, total_num+1):
        j = 22000+i
        url = f"http://127.0.0.1:{j}"
        web3 = Web3(Web3.HTTPProvider(url))
        print(f"Connected to port {j}")
        print(web3.isConnected())
        print(web3.eth.accounts[0])
        user_acct = web3.eth.accounts[0]
        print("User Account: ")
        print(user_acct)

        with open(file_name)as json_file:
            obj_file = json.load(json_file)
            obj = obj_file['objects']
            # 改成直接從區塊鏈上抓
            _acct = user_acct
            _obj = obj[i-4]['obj']
            _attr = obj[i-4]['attr']
            _wishlist = obj[i-4]['wishlist']
            register.get_url(url)
            register.run(_acct, _obj, _attr, _wishlist)
            time.sleep(1)


def no_match(file_name):
    # 與不同節點建立連線，抓取每個節點的帳號
    for i in range(env_num+1, total_num+1):
        j = 22000+i
        url = f"http://127.0.0.1:{j}"
        web3 = Web3(Web3.HTTPProvider(url))
        print(f"Connected to port {j}")
        print(web3.isConnected())
        print(web3.eth.accounts[0])
        user_acct = web3.eth.accounts[0]
        print("User Account: ")
        print(user_acct)

        with open(file_name)as json_file:
            obj_file = json.load(json_file)
            obj = obj_file['objects']
            # 改成直接從區塊鏈上抓
            _acct = user_acct
            _obj = obj[i-4]['obj']
            _attr = obj[i-4]['attr']
            _wishlist = obj[i-4]['wishlist']
            register.get_url(url)
            register.run(_acct, _obj, _attr, _wishlist)
            time.sleep(1)

            for k in range(9):
                no = str(int(_attr[1:]) + 1)
                _obj = no
                _attr = 'n' + no
                print("no: ", no)
                print(type(no))
                print("_obj:", _obj)
                print("_attr:", _attr)
                print("wishlist: ", _wishlist)
                print(type(_wishlist))

                register.get_url(url)
                register.run(_acct, _obj, _attr, _wishlist)
                time.sleep(1)


if __name__ == "__main__":
    # match('object_data_match1.json')
    # match('object_data_match2.json')
    # match('object_data_match3.json')
    # match('object_data_match4.json')
    no_match('object_data.json')
