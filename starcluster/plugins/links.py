import json
import os
import time
import posixpath
import re
import shutil

from starcluster import utils
from starcluster import static
from starcluster import spinner
from starcluster import exception
from starcluster.utils import print_timing
from starcluster.clustersetup import DefaultClusterSetup

from starcluster.logger import log

class Links(DefaultClusterSetup):

    def run(self, nodes, master, user, user_shell, volumes):

       for node in nodes:
            if node._alias == 'master':
                pass

            username = 'user' + node._alias[-3:]
            password = 'rcuser' + node._alias[-3:]
            print '\n'
            print 'username: {0}'.format(username)
            print 'url:      https://{0}'.format(node.dns_name)
            print 'password: {0}'.format(password)
            print 'nodename: {0}'.format(node._alias)
            print 'web:      http://http://researchcomputing.github.io/csdms_2014/'
            print '\n'
