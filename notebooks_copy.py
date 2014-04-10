#!/usr/bin/env python
import os
import sys
import subprocess
import argparse

def get_node(i):
	user = 'user{0:03d}'.format(i)
	node = 'node{0:03d}'.format(i)
	return user, node

def copy_directory(i, directory):
	user, node = get_node(int(i))
	cmd = 'su {0} -c "mkdir -p /home/{0}/{1}"'
	cmd = cmd.format(user, directory)
	print cmd
	pid = subprocess.Popen(cmd, shell=True)
	pid.wait()

	cmd = 'su {0} -c "cp -r /home/molu8455/{1}/* /home/{0}/{1}/"'
	cmd = cmd.format(user, directory)
	print cmd
	pid = subprocess.Popen(cmd, shell=True)
	pid.wait()

def get_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', help='directory: e.g. .ipython/profile_default/static/custom/',default='notebooks')
    parser.add_argument('-u', help='user', default=None)
    return parser.parse_args(argv)

if __name__ == '__main__':

	args = get_args(sys.argv[1:])

	if args.u is None:
		pass
	else:
		copy_directory(args.u, args.d)


# directory = 'notebooks'
# user = None
# try:
# 	user = int(sys.argv[1])
# except IndexError:
# 	pass

# if user is None:
# 	for i in range(1,19):
# 		copy_directory(i)
# else:
# 	copy_directory(user)
