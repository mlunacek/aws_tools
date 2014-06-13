#!/usr/bin/env python
import os
import sys
import subprocess
import argparse

def get_node(i):
	if i == 'molu8455':
		return 'molu8455', 'master'
	user = 'user{0:03d}'.format(i)
	node = 'node{0:03d}'.format(i)
	return user, node

def kill_all(i):
	user, node = get_node(i)

	cmd = 'ssh -n {0} "killall -9 -u {1}"'
	cmd = cmd.format(node, user)
	print cmd
	pid = subprocess.Popen(cmd, shell=True)
	pid.wait()

def nginx(i):
	user, node = get_node(i)

	cmd = 'ssh -n {0} "cp /home/{1}/tmp.conf /etc/nginx/conf.d/default.conf"'
	cmd = cmd.format(node, user)
	print cmd
	pid = subprocess.Popen(cmd, shell=True)
	pid.wait()

	cmd = 'ssh -n {0} "service nginx restart"'
	cmd = cmd.format(node, user)
	print cmd
	pid = subprocess.Popen(cmd, shell=True)
	pid.wait()

def notebook_config(i):
	user, node = get_node(i)
	cmd = 'su {0} -c "python /usr/local/aws_tools/scripts/notebooks_config.py"'
	cmd = cmd.format(user)
	print cmd
	pid = subprocess.Popen(cmd, shell=True)
	pid.wait()

def start_notebook(i):
	user, node = get_node(i)
	#ssh -f  -n {0} "su {1} -c 'cd /home/{1}; ipython notebook > /dev/null'"
	cmd = 'ssh -f  -n {0} '
	cmd = cmd + '"su {1} -c'
	cmd = cmd + '\'cd /home/{1}; /usr/local/anaconda/bin/ipython notebook >& /dev/null\'"'
	cmd = cmd.format(node, user)
	print cmd
	pid = subprocess.Popen(cmd, shell=True)
	pid.wait()

def restart_notebook(i):
	kill_all(i)
	notebook_config(i)
	nginx(i)
	start_notebook(i)

def get_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', help='user', default=None)
    return parser.parse_args(argv)

if __name__ == '__main__':

	args = get_args(sys.argv[1:])

	if args.u is None:
		for i in range(1,39):
			restart_notebook(i)
	if args.u == 'molu8455':
		restart_notebook(args.u)
	else:
		restart_notebook(int(args.u))
