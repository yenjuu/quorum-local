import os, sys
import json
import time
import errno
import pexpect
import pprint
import sqlite3
import secrets
import asyncio
import subprocess
from threading import Thread
from web3.providers.eth_tester import EthereumTesterProvider
from web3 import Web3
from web3.middleware import geth_poa_middleware

"""
只跑這個程式就部好除了動態部署的attribute contract 以外所有需要的合約
"""

# link to quorum
# quorum_url = "http://192.168.66.28:22000"
quorum_url = "http://127.0.0.1:22000"
# quorum_url = "https://ropsten.infura.io/v3/10193803ad6b40a5a39653a99614f6ed"

web3 = Web3(Web3.HTTPProvider(quorum_url))
web3.middleware_onion.inject(geth_poa_middleware, layer=0)
web3.eth.defaultAccount = web3.eth.accounts[0]
web3.parity.personal.unlock_account(web3.eth.accounts[0], "123", 15000)

gov_acct = web3.eth.accounts[0]


def run_command(command):
    p = subprocess.check_output(command, shell=True)
    result = p.decode(sys.stdout.encoding)
    return result


def change_dir(path):
    if os.getcwd() != path:
        print("Path before: " + os.getcwd())
        os.chdir(path)
        print("Path after: " + os.getcwd())
    else:
        print("Current path: " + os.getcwd())


def get_acct(env_num, total_num):
    change_dir("/home/quorum/quorum/fromscratch/")
    for i in range(1, total_num + 1):
        keystore = run_command(f"ls new-node-{i}/keystore").split("-")
        keystore = keystore[len(keystore) - 1].replace("\n", "")
        keystore = "0x"+keystore
        print(type(keystore))
        print("account: ", keystore)

        if (i - 1) > (env_num-1):
            user_acct.append(keystore)
        else:
            env_acct.append(keystore)
    global gov_acct
    gov_acct = env_acct[0]
    print("env acct: ")
    print(env_acct)
    print("gov acct: ")
    print(gov_acct)
    print("user acct: ")
    print(user_acct)


# load account from genesis.json
def reload_account():
    change_dir("/home/quorum/quorum_code")
    # write to object_data.json file, to add data
    with open("object_data.json", "r", encoding="utf8") as jfile:
        jdata = json.load(jfile)
    i = 0
    for obj in jdata["objects"]:
        if i < len(jdata["objects"]):
            obj["acct"] = user_acct[i]
            i += 1
            # print(obj['acct'])
            with open("object_data.json", "w", encoding="utf8") as jfile:
                json.dump(jdata, jfile, indent=4)


def db_link():
    # link to DB
    db_url = r"/home/quorum/quorum_code/sqlite/quorum.db"
    db_conn = sqlite3.connect(db_url)
    cur = db_conn.cursor()
    return (cur, db_conn)


def compile_contract(contract_source_file, contract_name=None):
    print(f"> Compiling contract..{contract_source_file} \n")
    # os.system(f"solc --bin {contract_source_file} > bin/{contract_name}.bin")
    # os.system(f"solc --abi {contract_source_file} > bin/{contract_name}.abi")
    os.system(
        f"solc --combined-json abi,bin {contract_source_file} > bin/{contract_name}.json"
    )

    compiled_file_path = f"{contract_source_file}:{contract_name}"

    with open(f"bin/{contract_name}.json") as json_file:
        compiled_sol = json.load(json_file)
        abi = compiled_sol["contracts"][compiled_file_path]["abi"]
        bytecode = compiled_sol["contracts"][compiled_file_path]["bin"]

    return abi, bytecode


def deploy_contract(acct, abi, bytecode, contract_name):
    print(f"> Deploying {contract_name} contract.. \n")
    abi = json.loads(abi)
    contract_interface = web3.eth.contract(abi=abi, bytecode=bytecode)
    tx_hash = contract_interface.constructor().transact()
    tx_receipt = web3.eth.waitForTransactionReceipt(tx_hash)
    contract = web3.eth.contract(address=tx_receipt.contractAddress, abi=abi)
    address = str(contract.address)
    abi = str(contract.abi)
    print(f"> Was {contract_name} contract deploy successful? ")
    pprint.pprint(tx_receipt["status"])
    print("> BlockNumber: ")
    pprint.pprint(tx_receipt["blockNumber"])
    print(f"> {contract_name} contract address: \n" + contract.address)

    return contract_name, address, abi


def saveToDB(contract_name, address, abi):
    cur, db_conn = db_link()
    # save contract data into DB
    cur.execute(
        "insert into contract_data(contract_name, abi, address) values (?, ?, ?)",
        (contract_name, abi, address),
    )
    db_conn.commit()
    db_conn.close()


def delete_db(contract_name):
    cur, db_conn = db_link()
    # contract_name = str(input())
    print("Delete contract: " + contract_name)
    cur.execute("DELETE FROM contract_data WHERE contract_name=(?)", [contract_name])
    db_conn.commit()
    db_conn.close()


def initialization(contract_name):
    # 驅動此程式部署所有初始化所需之合約
    contract_list = ["registered.sol", "attrRecord.sol", "whitelist.sol"]
    bin_list = ["registered.json", "attrRecord.json", "whitelist.json"]
    for filename in os.listdir("./contract"):
        if filename not in contract_list:
            os.system(f"rm ./contract/{filename}")
    for filename in os.listdir("./bin"):
        if filename not in bin_list:
            os.system(f"rm ./bin/{filename}")

    contract_source_file = f"contract/{contract_name}.sol"

    # compile contract
    abi, bytecode = compile_contract(contract_source_file, contract_name)
    # deploy contract
    contract_name, address, abi = deploy_contract(
        gov_acct, abi, bytecode, contract_name
    )
    saveToDB(contract_name, address, abi)


def redo(contract_name=None):
    contract_list = ["registered", "attrRecord", "whitelist"]
    for contract_name in contract_list:
        delete_db(contract_name)
        initialization(contract_name)


if __name__ == "__main__":
    # get_acct(3, 7)
    # reload_account()
    redo()
