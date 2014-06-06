aws tools
=========

Tools for managing ipython notebooks on AWS clusters.

## Starcluster Setup

- Download and install [starcluster](http://star.mit.edu/cluster/docs/0.93.3/installation.html).
- Copy the `starcluster/config.template to `.starcluster/conifg` and modify the parameters.
- Copy the `starcluster/plugins` directory to `.starcluster/plugins` and add `~/.starcluster/plugins` to your $PYTHONPATH.

## Start the cluster

- Start the instances.

    starcluster start mycluster

- Configure ssh and create the users.

    starcluster runplugin createusers mycluster

- Modify your .ssh/config file (optional)

    starcluster runplugin sshconfig mycluster

    Host aws
        HostName ec2-54-213-38-30.us-west-2.compute.amazonaws.com
        IdentityFile ~/.ssh/awswest.pem
        User molu8455

    Host awsroot
        HostName ec2-54-213-38-30.us-west-2.compute.amazonaws.com
        IdentityFile ~/.ssh/awswest.pem
        User root

- Start the notebooks, configure passwords, setup nginx.

    starcluster runplugin notebooks mycluster

- Print a list of links.

    starcluster runplugin links mycluster


    >>> Running plugin links

    username: userter
    url:      https://ec2-54-213-38-30.us-west-2.compute.amazonaws.com
    password: rcuserter
    nodename: master
    web:      http://http://researchcomputing.github.io/csdms_2014/

    username: user001
    url:      https://ec2-54-186-237-94.us-west-2.compute.amazonaws.com
    password: rcuser001
    nodename: node001
    web:      http://http://researchcomputing.github.io/csdms_2014/


## Managing the notebooks

Login as root and clone the repository.

    starcluster sshmaster mycluster

or

    ssh awsroot

if using the `.ssh/config`. Then clone the repo and add scripts to path.

    cd /user/local
    git clone https://github.com/mlunacek/aws_tools.git
    export PATH=/usr/local/aws_tools/scripts/:$PATH
    chmod 755 /usr/local/aws_tools/scripts/*.py


### Restart examples

Restart user001 notebook:

    notebooks_restart.py -u 1

Restart molu8455 notebook:

    notebooks_restart.py -u molu8455

Restart all notebooks:

    notebooks_restart.py

### Copy files

Copy files from /home/molu8455/notebooks to a user's notebooks directory.

    notebooks_copy.py -u 1

output

    su user001 -c "mkdir -p /home/user001/notebooks"
    su user001 -c "cp -r /home/molu8455/notebooks/* /home/user001/notebooks/"

Another example.

    notebooks_copy.py  -u 1 -d .ipython/profile_default

All users

    python /home/molu8455/aws_tools/notebooks_copy.py  -d notebooks
