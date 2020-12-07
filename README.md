## Environment setting

### Using Ganache

1. Create virtualenv and install library

   ```bash
   virtualenv -p ~/.pyenv/versions/3.8.5/bin/python venv
   pip install --upgrade web3
   pip install flask
   ```
   Or you can just run `installLib.sh` to install all library you need.



2. Change your node.js version to 12 (Version 14 has some issue to start ganache-cli, is still not fixed.)

   ```bash
   nvm use 12
   ```

   

3. Start ganache-cil

   ```bash
   ganache-cli -p 7545 -q
   ```

4. Download `solc` to compile solidity file in local.
   ```bash
   sudo add-apt-repository ppa:ethereum/ethereum
   sudo apt-get update
   sudo apt-get install solc
   ```

### Build Quorum locally   
1. Run `add_node_raft.py`: Will clone the Quorum repo, build, and add 13 nodes on local.
2. Go to your cloned `quorum/fromscratch` file and run `geth` by `./startnode.sh` to start all nodes.
3. Run `addPeer.py` file to add other peers automatically into quorum network through command line.

And DONE!

### Blockchain note
[Some notes about blockchain](https://hackmd.io/@arielchen/HyrsSK8TL)