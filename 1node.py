#!/Users/ariel/quorum-local/.pyenv/shims/python
import os
import subprocess
import pexpect

os.system("killall geth")
os.chdir("/Users/ariel/quorum-local")
cmd = "sudo rm -r quorum"
child = pexpect.spawn(cmd)
child.expect("password")
child.sendline("123")
child.interact()

os.system("cp -r Desktop/quorum_1node/ quorum")
os.popen("sh /Users/ariel/quorum-local/quorum/fromscratch/startnode.sh")
os.system("ps")
