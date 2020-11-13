#!/Users/ariel/quorum-local/.pyenv/shims/python

import os
import sys
import json
import time
import errno
import pexpect
import subprocess

# 建立node資料夾
# 新增帳號＆把 節點編號、帳號、密碼 記到.json


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


def autofill(cmd):
    child = pexpect.spawn(cmd)
    child.expect("Password")
    child.sendline("123")
    child.expect("Repeat password")
    child.sendline("123")
    # print(child.before)
    child.interact()


def add_node_cmd(node_num):
    # TODO: 測能不能在raft裡成功新增節點
    i = node_num+1
    command = f"cat /Users/ariel/quorum-local/quorum/fromscratch/new-node-{i}/enode"
    enode_id = run_command(command).replace("\n", "")
    enode_url = (
        f"enode://{enode_id}@127.0.0.1:{21000+i-1}?discport=0&raftport={50000+i-1}"
    )

    cmd = f"geth attach new-node-{node_num}/geth.ipc"
    child = pexpect.spawn(cmd)
    child.expect(">")
    try:
        child.sendline(f"raft.addPeer('{enode_url}')")
    except OSError as exc:
        if exc.errno != errno.EEXIST:
            raise
        child.sendline("exit")
        child.interact()


def edit_genesis(keystore):
    change_dir("/Users/ariel/quorum-local/quorum/fromscratch")

    keystore = "0x" + keystore
    print(keystore)
    try:
        with open(f"genesis.json", "r", encoding="utf8") as jfile:
            jdata = json.load(jfile)
            print(type(jdata["alloc"]))
            print(jdata["alloc"])
            alloc = jdata["alloc"]
        with open(f"genesis.json", "w", encoding="utf8") as jfile:

            d1 = {keystore: {"balance": "2000000000000000000000000000"}}
            alloc.update(d1)
            json.dump(jdata, jfile, indent=4)

        # print("> ls\n" + run_command("ls"))
    except OSError:
        print("genesis.json not exist.")


def gen_key(i):
    change_dir("/Users/ariel/quorum-local/quorum/fromscratch")
    os.system(f"bootnode --genkey=nodekey{i}")
    os.system(f"mv nodekey{i} new-node-{i}/nodekey")
    os.system(
        f"bootnode --nodekey=new-node-{i}/nodekey --writeaddress > new-node-{i}/enode"
    )
    # 先改 後複製
    # 抓命令行輸出的結果
    command = f"cat new-node-{i}/enode"
    enode_id = run_command(command).replace("\n", "")
    print(enode_id)
    with open(f"new-node-{i-1}/static-nodes.json", "r", encoding="utf8") as jfile:
        jdata = json.load(jfile)
        jdata.append(
            f"enode://{enode_id}@127.0.0.1:{21000+i-1}?discport=0&raftport={50000+i-1}"
        )
        print(jdata)
    with open(f"new-node-{i}/static-nodes.json", "w", encoding="utf8") as jfile:
        json.dump(jdata, jfile, indent=4)
    # os.system(f"cp static-nodes.json new-node-{i}")
    enode_url = (
        f"enode://{enode_id}@127.0.0.1:{21000+i-1}?discport=0&raftport={50000+i-1}"
    )
    return enode_url


def init_node(i):
    change_dir("/Users/ariel/quorum-local/quorum/fromscratch")
    try:
        os.system(f"geth --datadir new-node-{i} init genesis.json")
    except OSError:
        print("Init new node failed.")


def init():
    """
    建立初始節點
    """

    os.chdir("/Users/ariel/quorum-local")
    os.system("git clone https://github.com/ConsenSys/quorum.git")
    os.chdir(os.getcwd() + "/quorum/")
    # os.chdir("~/quorum/")
    os.system("make all")

    # NOTE: Change PATH (先直接下指令改路徑)
    path = R"${pwd}/build/bin:$PATH"
    os.path.expandvars(path)
    # os.system("export PATH=$(pwd)/build/bin:$PATH")

    os.system("mkdir fromscratch")

    # subprocess.Popen(['mkdir new-node-1', cwd="~/quorum/fromscratch/"])
    os.chdir(os.getcwd() + "/fromscratch/")
    # os.chdir('~/quorum/fromscratch/')

    # Create new account & folder
    os.system("mkdir new-node-1")

    cmd = "geth --datadir new-node-1 account new"
    autofill(cmd)
    keystore = run_command("ls new-node-1/keystore").split("-")
    keystore = keystore[len(keystore) - 1].replace("\n", "")
    print(type(keystore))
    print("account: ", keystore)

    os.system(
        "cp /Users/ariel/quorum-local/quorum_template/genesis_template.json genesis.json")
    edit_genesis(keystore)

    # Create enode_id & Edit static-node.json
    os.system(
        "cp /Users/ariel/quorum-local/quorum_template/static-nodes_template.json static-nodes.json"
    )
    # ADD NODEKEY
    os.system("bootnode --genkey=nodekey")
    os.system("cp nodekey new-node-1/")
    os.system(
        "bootnode --nodekey=new-node-1/nodekey --writeaddress > new-node-1/enode")

    command = "cat new-node-1/enode"
    enode_id = run_command(command).replace("\n", "")
    print(enode_id)
    with open(f"static-nodes.json", "r", encoding="utf8") as jfile:
        jdata = json.load(jfile)
        jdata.append(
            f"enode://{enode_id}@127.0.0.1:21000?discport=0&raftport=50000")
        print(jdata)
    with open(f"static-nodes.json", "w", encoding="utf8") as jfile:
        json.dump(jdata, jfile, indent=4)
    os.system(f"cp static-nodes.json new-node-1")

    # INIT NEW NODE
    init_node(1)
    os.system("mkdir log")
    # Edit startnode.sh
    os.system(
        "cp /Users/ariel/quorum-local/quorum_template/startnode_template.sh startnode.sh")
    # print("> ls\n" + run_command("ls -al"))
    os.system("chmod +x startnode.sh")
    # print("> ls\n" + run_command("ls -al"))


def add_node(num):
    """添加其餘節點

    Args:
        num (int): 輸入總節點數
    """
    change_dir("/Users/ariel/quorum-local/quorum/fromscratch")

    for i in range(2, num + 1):
        try:
            os.system(f"mkdir new-node-{i}")
            # New ethereum account
            cmd = f"geth --datadir new-node-{i} account new"
            autofill(cmd)
            # Get new account address
            keystore = run_command(f"ls new-node-{i}/keystore").split("-")
            keystore = keystore[len(keystore) - 1].replace("\n", "")
            print(type(keystore))
            print("account: ", keystore)
            # edit_genesis(keystore)
            # ADD NODEKEY
            enode_url = gen_key(i)

            # Init new node
            init_node(i)

            # Edit startnode.sh
            with open(f"startnode.sh", "a+", encoding="utf8") as jfile:
                jfile.write("\n")
                # jfile.write(f"PRIVATE_CONFIG=ignore nohup geth --datadir new-node-{i} --nodiscover --verbosity 5 --networkid 31337 --raft --raftport {50000+i-1} --raftjoinexisting {i} --rpc --rpcaddr 0.0.0.0 --rpcport {22000+i-1} --rpcapi admin,db,eth,debug,miner,net,shh,txpool,personal,web3,quorum,raft --emitcheckpoints --port {21000+i-1} 2>>node{i}.log &")
                # jfile.write(f"PRIVATE_CONFIG=ignore nohup geth --datadir new-node-{i} --verbosity 5 --networkid 31337 --raft --raftport {50000+i-1} --raftjoinexisting {i} --rpc --rpcaddr 0.0.0.0 --rpcport {22000+i-1} --rpcapi admin,db,eth,debug,miner,net,shh,txpool,personal,web3,quorum,raft --bootnodes --emitcheckpoints --port {21000+i-1} 2>>node{i}.log &")
                jfile.write(
                    f"PRIVATE_CONFIG=ignore nohup geth --datadir new-node-{i} --nodiscover --verbosity 5 --networkid 31337 --raft --raftport {50000+i-1} --raftjoinexisting {i} --rpc --rpcaddr 0.0.0.0 --rpcport {22001+i-1} --rpcapi admin,db,eth,debug,miner,net,shh,txpool,personal,web3,quorum,raft --allow-insecure-unlock --emitcheckpoints --port {21000+i-1} 2>>log/node{i}.log &"
                )
                jfile.write("\n")
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise
            pass

    # 停掉初始節點，把所有節點都啟動後將節點加入
    # run_command("killall geth")
    # change_dir("/Users/ariel/quorum-local/quorum/fromscratch")
    # run_command("./startnode.sh")
    # os.system("ps")
    # cmd in geth & Add node to node1
    # for i in range(2, num+1):
    #     add_node_cmd(i-1)


# 生成節點，並複製到datadir
if __name__ == "__main__":
    # init()
    total_num = 13
    add_node(total_num)

    run_command("killall geth")
    time.sleep(1)
    os.popen("sh /Users/ariel/quorum-local/quorum/fromscratch/startnode.sh")
    os.system("ps")
    # cmd in geth & Add node to node1
    for i in range(2, total_num+1):
        add_node_cmd(i-1)
