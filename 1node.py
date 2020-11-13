#!/home/quorum/.pyenv/shims/python
import os
import subprocess
import pexpect

os.system("killall geth")
os.chdir("/home/quorum")
cmd = "sudo rm -r quorum"
child = pexpect.spawn(cmd)
child.expect("password")
child.sendline("123")
child.interact()

os.system("cp -r Desktop/quorum_1node/ quorum")
# os.chdir("/home/quorum/quorum/fromscratch")
# print(os.getcwd())
# subprocess.run('/home/quorum/quorum/fromscratc/startnode.sh', shell=True, check=True, timeout=10)
os.popen("sh /home/quorum/quorum/fromscratch/startnode.sh")
os.system("ps")
