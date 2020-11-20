#!/Users/ariel/quorum-local/.pyenv/shims/python

import os
import sys
import json
import time
import errno
import pexpect
import subprocess

# quorum_url = "http://127.0.0.1:22000"

# web3 = Web3(Web3.HTTPProvider(quorum_url))
# #web3.middleware_onion.inject(geth_poa_middleware, layer=0)
# web3.eth.defaultAccount = web3.eth.accounts[0]
# #web3.parity.personal.unlock_account(web3.eth.accounts[0], "123", 15000)


def run_command(command):
    p = subprocess.check_output(command, shell=True)
    result = p.decode(sys.stdout.encoding)
    return result


def add_node_cmd(node_num):
    # TODO: 測能不能在raft裡成功新增節點
    command = f"cat /Users/ariel/quorum-local/quorum/fromscratch/new-node-{node_num+1}/enode"
    enode_id = run_command(command).replace("\n", "")
    enode_url = f"enode://{enode_id}@127.0.0.1:{21000+node_num}?discport=0&raftport={50000+node_num}"

    cmd = f"geth attach /Users/ariel/quorum-local/quorum/fromscratch/new-node-{node_num}/geth.ipc"
    child = pexpect.spawn(cmd)
    child.expect(">")
    child.sendline(f"raft.addPeer('{enode_url}')")
    child.sendline("exit")
    child.interact()


if __name__ == "__main__":
    # init()
    total_num = 13
    # add_node(total_num)

    # run_command("killall geth")
    # time.sleep(1)
    # os.popen("sh /Users/ariel/quorum-local/quorum/fromscratch/startnode.sh")
    # os.system("ps")
    # cmd in geth & Add node to node1
    for i in range(2, total_num + 1):
        add_node_cmd(i - 1)
        time.sleep(1)
