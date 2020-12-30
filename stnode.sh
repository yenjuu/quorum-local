#! /bin/bash

# killall geth
quorum_dir="/Users/ariel/quorum-local/quorum/fromscratch"
code_dir="/Users/ariel/quorum-local"
cd ${quorum_dir}
./startnode.sh
cd ${code_dir}
echo 'starting nodes...'
