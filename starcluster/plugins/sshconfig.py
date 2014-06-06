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

class SSHConfig(DefaultClusterSetup):

    def __init__(self, ssh_config=None):
        self._ssh_config = ssh_config
        super(SSHConfig, self).__init__()

    def run(self, nodes, master, user, user_shell, volumes):

        # Make a backup copy
        with open(self._ssh_config,'r') as infile:
            data = infile.read()

        tmp = re.sub(r'ec2-[0-9]+-[0-9]+-[0-9]+-[0-9]+.us-west-2.compute.amazonaws.com', master.dns_name, data)

        with open(self._ssh_config, 'w') as outfile:
            outfile.write(tmp)
