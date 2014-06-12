#!/usr/bin/env python

import subprocess
import sys
import os
from functools import partial
import time

def move_python(hostname):
  cmd = 'ssh {0} "mv -n /usr/local/anaconda /mnt; ln -s /mnt/anaconda /usr/local/"'.format(hostname)
  print cmd
  pid = subprocess.Popen(cmd, shell=True,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)
  return pid

def move_spark(hostname):
  cmd = 'ssh {0} "mv -n /opt/spark /mnt; ln -s /mnt/spark /opt/"'.format(hostname)
  print cmd
  pid = subprocess.Popen(cmd, shell=True,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)
  return pid

def wait(pid):
  pid.wait()
  out, err = pid.communicate()
  return out, err

def create_host(i):
  return 'node{0:03d}'.format(i)

hosts = map(create_host, range(1,40))
print hosts

hostlist = ['master']
hostlist.extend(hosts)

tic = time.time()
res = map(move_python, hostlist)
print 'moving python'
print len(res)
tmp = map(wait, res)
print time.time()-tic, 'sec'

tic = time.time()
res = map(move_spark, hostlist)
print 'moving spark'
print len(res)
tmp = map(wait, res)
print time.time()-tic, 'sec'
