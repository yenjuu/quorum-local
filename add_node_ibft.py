#! /path/python

import os
import sys
import json
import errno
import pexpect
import subprocess

"""
Add node shell with IBFT consensus
"""

home_path = "/home/quorum"
ibftTool_path = f"{home_path}/quorum/fromscratchistanbul/istanbul-tools"


def run_command(cmd):
    p = subprocess.check_output(cmd, shell=True)
    result = p.decode(sys.stdout.encoding)
    return result


def change_dir(path):
    try:
        if (os.getcwd() != path):
            print("Path before: "+os.getcwd())
            os.chdir(path)
            print("Path after: " + os.getcwd())
        else:
            print("Current path: " + os.getcwd())
    except OSError as exc:
        if exc.errno != errno.EEXIST:
            raise
        pass


def autofill_pwd(cmd):
    child = pexpect.spawn(cmd)
    child.expect('Passphrase')
    child.sendline('123')
    child.expect('Repeat passphrase')
    child.sendline('123')
    # print(child.before)
    child.interact()


def init(num):

    change_dir(home_path)
    os.system("git clone https://github.com/ConsenSys/quorum.git")
    change_dir(f"{home_path}/quorum")
    os.system("make all")
    # export path
    # export PATH=$(pwd)/build/bin:$PATH

    # Install istanbul-tools
    os.system("mkdir fromscratchistanbul")
    change_dir(f"{home_path}/quorum/fromscratchistanbul")
    os.system("git clone https://github.com/ConsenSys/istanbul-tools.git")
    change_dir(f"{home_path}/quorum/fromscratchistanbul/istanbul-tools")
    os.system("make")

    # Create folders of validator nodes
    for i in range(num):
        os.system("mkdir node{i}")

    # Change into lead node folder and generate the setup file
    change_dir(f"{ibftTool_path}/node0")
    result = run_command(
        f"{ibftTool_path}/build/bin/istanbul setup --num {num} --nodes --quorum --save --verbose")
    print(result)

    # Create geth folder in each validator nodes' folder
    change_dir(f"{ibftTool_path}")
    for i in range(num):
        os.system(f"mkdir -p node{i}/data/geth")
    # Generate initial account for each nodes
        cmd = f"geth --datadir node{i}/data account new"
        autofill_pwd(cmd)
    # To add accounts to the initial block, edit the genesis.json file in the lead node’s working directory
    # 但好像已經自動新增進去了，可能在初始多個節點之後要再新增節點才需要手動加
    result = run_command("vim node0/genesis.json")
    print(result)

    # Copy genesis.json, static-nodes.json, nodekey to each node folder
    for i in range(num):
        os.system(f"cp node0/genesis.json node{i+1}")
        os.system(f"cp node0/static-nodes.json node{i}/data/")
        os.system(f"cp node0/{i}/nodekey node{i}/data/geth")

    # Switch into each node and initialize
        change_dir(f"{ibftTool_path}/node{i}")
        os.system("geth --datadir data init genesis.json")

    # Create a script to start all node
    change_dir(f"{ibftTool_path}")
    file = open("startall.sh", "w")
    for i in range(num):
        file.write("#!/bin/bash")
        file.write(f"cd ../node{i}")
        file.write(
            f"PRIVATE_CONFIG=ignore nohup geth --datadir data --nodiscover --istanbul.blockperiod 5 --syncmode full --mine --minerthreads 1 --verbosity 5 --networkid 10 --rpc --rpcaddr 0.0.0.0 --rpcport {22000+i} --rpcapi admin,db,eth,debug,miner,net,shh,txpool,personal,web3,quorum,istanbul --emitcheckpoints --port {30300+i} 2>>node.log &")
    file.close()

    os.system("chmod +x startall.sh")


if __name__ == "__main__":
    init(5)
