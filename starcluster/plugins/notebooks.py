import json
import os
import posixpath
import re
import jinja2 as jin

from starcluster import static
from starcluster.clustersetup import DefaultClusterSetup
from starcluster.logger import log

nginx_template = jin.Template('''
server {
    listen       443;
    ssl on;
    ssl_certificate {{ssl_cert}};
    ssl_certificate_key {{ssl_cert}};

    server_name  localhost;

    location / {

        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-NginX-Proxy true;

        proxy_pass https://127.0.0.1:8888;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    error_page   500 502 503 504  /50x.html;
    location = /50x.html {
        root   /usr/share/nginx/html;
    }
}
''')

html_template = jin.Template('''
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN">
<html lang="en">
    <head>
        <title>Research Computing CU Boulder AWS Instances</title>
        <style>
            th{
                text-align:left;
                border-bottom: 1px solid #ebebeb;
            }

            hr {
              height: 1px;
              line-height: 1px;
              margin-top: 1em;
              padding-bottom: 1em;
              border: none;
            }

            td {
              border-bottom: 1px solid #ebebeb;
              text-align: left;
            }

            body{
                margin-left: auto;
                margin-right: auto;
                width: 800px;
            }
        </style>
    </head>
    <body>
    <img src=https://www.rc.colorado.edu/sites/all/themes/research/logo.png>

    <table style="width:700px">
        <tr>
            <th>USER</th>
            <th>URL</th>
            <th>PASSWORD</th>
        </tr>
        {% for user in data %}
            <tr>
            <td> {{ user }} </td>
            <td><a href="{{data[user].url}}" target="_blank">{{data[user].url}}</a></td>
            <td>{{data[user].password}}</td>
            </tr>
        {% endfor %}

    </table>
    </body>
</html>
''')

def get_users(master):
    f = master.ssh.remote_file('/etc/passwd','r')
    data = f.read()
    f.close()
    return list(set(re.findall(r'(user[0-9]{3})', data)))

def stop_notebooks(node):
    node.ssh.execute("pkill -f python", ignore_exit_status=True)
    node.ssh.execute("pkill -f ipython", ignore_exit_status=True)
    log.info("Stopping ipython on %s" % node.dns_name)

def get_node_index(nodelist, alias):
    for i, n in enumerate(nodelist):
        if n._alias == alias:
            return i
    return None

class CopyNotebooks(DefaultClusterSetup):

    def __init__(self, notebook_dir=None, profile_dir=None):
        self._notebook_dir = notebook_dir
        self._profile_dir = profile_dir
        super(CopyNotebooks, self).__init__()

    def run(self, nodes, master, user, user_shell, volumes):
        self._nodes = nodes
        self._master = master
        self._user = user
        self._user_shell = user_shell
        self._volumes = volumes
        self._users = get_users(self._master)

        print self._notebook_dir
        print self._profile_dir

        #Upload once to user and then copy to other 'created' users
        self.copy_local(self._notebook_dir, '/home/{0}'.format(self._user))
        self.copy_remote('notebooks')

        #Copy style to master
        self.copy_local(self._profile_dir, '/home/{0}/.ipython/profile_default'.format(self._user))

    def copy_remote(self, directory):
        src_dir = '/home/{0}/{1}'.format(self._user, directory)
        for user in self._users:
            self._master.ssh.switch_user(user)
            dest_dir = '/home/{0}/{1}'.format(user, directory)
            self._master.ssh.execute('mkdir -p {0}'.format(dest_dir))
            cmd = 'cp -r {0}/* {1}/'.format(src_dir, dest_dir)
            log.info(cmd)
            self._master.ssh.execute(cmd)
            self._master.ssh.switch_user('root')

    def copy_local(self, remote_dir, local_dir):
        self._master.ssh.switch_user(self._user)
        self._master.ssh.put(remote_dir, local_dir)
        self._master.ssh.switch_user('root')


class StopNotebooks(DefaultClusterSetup):
    def run(self, nodes, master, user, user_shell, volumes):
        for node in nodes:
            stop_notebooks(node)
            #log.info("Stopping ipython on %s" % node.dns_name)

class RestartNotebooks(DefaultClusterSetup):

    def run(self, nodes, master, user, user_shell, volumes):
        self._nodes = nodes
        self._master = master
        self._user = user
        self._user_shell = user_shell
        self._volumes = volumes
        self._users = get_users(self._master)

        self._data = {}

class Notebooks(DefaultClusterSetup):

    DOWNLOAD_JSON = os.path.join(static.STARCLUSTER_CFG_DIR, 'notebooks.json')
    DOWNLOAD_HTML = os.path.join(static.STARCLUSTER_CFG_DIR, 'notebooks.html')
    USER = 'user001'

    def __init__(self, download_json=None, download_html=None, user='user001'):
        self._download_json = download_json or self.DOWNLOAD_JSON
        self._download_html = download_html or self.DOWNLOAD_HTML
        self._userin = user

        super(Notebooks, self).__init__()

    def run(self, nodes, master, user, user_shell, volumes):
        self._nodes = nodes
        self._master = master
        self._user = user
        self._user_shell = user_shell
        self._volumes = volumes
        self._users = get_users(self._master)

        self._data = {}
        user = self._userin
        alias = 'node' + user[-3:]

        print user
        print alias
        node_index = get_node_index(self.nodes, alias)
        node = self.nodes[node_index]

        print node._alias
        print user
        stop_notebooks(node)
        user_home = master.getpwnam(user).pw_dir
        profile_dir = posixpath.join(user_home, '.ipython', 'profile_default')
        notebook_dir = posixpath.join(user_home, 'notebooks')

        self._create_profile(user, profile_dir)
        node.ssh.switch_user(user)
        self._start_notebook(node, user, profile_dir, notebook_dir)
        node.ssh.switch_user('root')
        self.save_output()

    def save_output(self):

        with open(self._download_json,'w') as outfile:
            outfile.write(json.dumps(self._data))

        with open(self._download_html, 'w') as outfile:
            outfile.write(html_template.render(data=self._data))


    def default_user(self):
        stop_notebooks(self._master)
        user_home = self._master.getpwnam(self._user).pw_dir
        profile_dir = posixpath.join(user_home, '.ipython', 'profile_default')
        notebook_dir = posixpath.join(user_home, 'notebooks')
        self._create_profile(self._user, profile_dir)
        self._master.ssh.switch_user(self._user)
        self._start_notebook(self._master, self._user, profile_dir, notebook_dir)
        self._master.ssh.switch_user('root')

    def _create_profile(self, user, profile_dir):
        """Create cluster configuration files."""
        log.info("Writing IPython cluster config files")
        self._master.ssh.switch_user(user)
        self._master.ssh.execute("rm -rf '%s'" % profile_dir)
        self._master.ssh.execute('ipython profile create')
        # Add startup files

        self._master.ssh.switch_user('root')

    def _start_notebook(self, node, user, profile_dir, notebook_directory):
        log.info("Setting up IPython web notebook for user: %s" % user)
        user_cert = posixpath.join(profile_dir, '%s.pem' % user)
        ssl_cert = posixpath.join(profile_dir, '%s.pem' % user)
        if not node.ssh.isfile(user_cert):
            log.info("Creating SSL certificate for user %s" % user)
            ssl_subj = "/C=US/ST=SC/L=STAR/O=Dis/CN=%s" % node.dns_name
            node.ssh.execute(
                "openssl req -new -newkey rsa:4096 -days 365 "
                '-nodes -x509 -subj %s -keyout %s -out %s' %
                (ssl_subj, ssl_cert, ssl_cert))
            log.info("DONE")
        else:
            log.info("Using existing SSL certificate...")
        f = node.ssh.remote_file('%s/ipython_notebook_config.py' %
                                   profile_dir)
        notebook_port = 8888
        notebook_passwd = 'rc' + user
        sha1py = 'from IPython.lib import passwd; print passwd("%s")'
        sha1cmd = "python -c '%s'" % sha1py
        sha1pass = node.ssh.execute(sha1cmd % notebook_passwd)[0]
        f.write('\n'.join([
            "c = get_config()",
            "c.IPKernelApp.pylab = 'inline'",
            "c.NotebookApp.certfile = u'%s'" % ssl_cert,
            "c.NotebookApp.ip = '*'",
            "c.NotebookApp.open_browser = False",
            "c.NotebookApp.password = u'%s'" % sha1pass,
            "c.NotebookApp.port = %d" % notebook_port,
            "c.NotebookApp.trust_xheaders = True"
            #"c.NotebookApp.base_project_url = '/notebook/'",
            # "c.NotebookApp.base_kernel_url = '/notebook/'",
            # "c.NotebookApp.webapp_settings = {'static_url_prefix':'/notebook/static/'}"
        ]))
        f.close()

        if notebook_directory is not None:
            if not node.ssh.path_exists(notebook_directory):
                node.ssh.makedirs(notebook_directory)
            node.ssh.execute_async(
                "ipython notebook --no-browser --notebook-dir='%s'"
                % notebook_directory)
        else:
            node.ssh.execute_async("ipython notebook --no-browser")

        self._authorize_port(node, notebook_port, 'notebook')
        self._authorize_port(node, 443, 'https')
        self._nginx_conf(node, user, ssl_cert)

        url = 'https://{0}'.format(node.dns_name)
        urlport = 'https://{0}:{1}'.format(node.dns_name, notebook_port)
        log.info('IPython notebook URL:     %s'% (url))
        log.info('The notebook password is: %s'% (notebook_passwd))
        #tunnel = 'ssh -i {2} -L 2000:localhost:8888  -f -N {0}@{1}'
        #tunnel = tunnel.format(user,node.dns_name, user+'.rsa')
        self._data[user] = {'password': notebook_passwd,
                            'url': url,
                            'urlport': urlport}

    def _nginx_conf(self, node, user, ssl_cert):
        node.ssh.switch_user('root')
        f = node.ssh.remote_file('/etc/nginx/conf.d/default.conf', 'w')
        tmp = nginx_template.render({'ssl_cert': ssl_cert})
        f.write(tmp)
        f.close()
        node.ssh.execute('service nginx restart')
        node.ssh.switch_user(user)

    def _authorize_port(self, node, port, service_name, protocol='tcp'):
        group = node.cluster_groups[0]
        world_cidr = '0.0.0.0/0'
        if isinstance(port, tuple):
            port_min, port_max = port
        else:
            port_min, port_max = port, port
        port_open = node.ec2.has_permission(group, protocol, port_min,
                                            port_max, world_cidr)
        if not port_open:
            log.info("Authorizing tcp ports [%s-%s] on %s for: %s" %
                     (port_min, port_max, world_cidr, service_name))
            node.ec2.conn.authorize_security_group(
                group_id=group.id, ip_protocol='tcp', from_port=port_min,
                to_port=port_max, cidr_ip=world_cidr)


class NotebooksAll(DefaultClusterSetup):

    DOWNLOAD_JSON = os.path.join(static.STARCLUSTER_CFG_DIR, 'notebooks.json')
    DOWNLOAD_HTML = os.path.join(static.STARCLUSTER_CFG_DIR, 'notebooks.html')

    def __init__(self, download_json=None, download_html=None):
        self._download_json = download_json or self.DOWNLOAD_JSON
        self._download_html = download_html or self.DOWNLOAD_HTML

        super(NotebooksAll, self).__init__()

    def run(self, nodes, master, user, user_shell, volumes):
        self._nodes = nodes
        self._master = master
        self._user = user
        self._user_shell = user_shell
        self._volumes = volumes
        self._users = get_users(self._master)

        self._data = {}

        # change this to workers
        for user in sorted(self._users):

            alias = 'node' + user[-3:]
            node_index = get_node_index(self.nodes, alias)
            if node_index is not None:
                node = self.nodes[node_index]

                stop_notebooks(node)
                user_home = master.getpwnam(user).pw_dir
                profile_dir = posixpath.join(user_home, '.ipython', 'profile_default')
                notebook_dir = posixpath.join(user_home, 'notebooks')

                self._create_profile(user, profile_dir)
                node.ssh.switch_user(user)
                self._start_notebook(node, user, profile_dir, notebook_dir)
                node.ssh.switch_user('root')

        self.default_user()
        # Save the output as json and html
        self.save_output()

    def save_output(self):

        with open(self._download_json,'w') as outfile:
            outfile.write(json.dumps(self._data))

        with open(self._download_html, 'w') as outfile:
            outfile.write(html_template.render(data=self._data))


    def default_user(self):
        stop_notebooks(self._master)
        user_home = self._master.getpwnam(self._user).pw_dir
        profile_dir = posixpath.join(user_home, '.ipython', 'profile_default')
        notebook_dir = posixpath.join(user_home, 'notebooks')
        self._create_profile(self._user, profile_dir)
        self._master.ssh.switch_user(self._user)
        self._start_notebook(self._master, self._user, profile_dir, notebook_dir)
        self._master.ssh.switch_user('root')

    def _create_profile(self, user, profile_dir):
        """Create cluster configuration files."""
        log.info("Writing IPython cluster config files")
        self._master.ssh.switch_user(user)
        self._master.ssh.execute("rm -rf '%s'" % profile_dir)
        self._master.ssh.execute('ipython profile create')
        self._master.ssh.switch_user('root')

    def _start_notebook(self, node, user, profile_dir, notebook_directory):
        log.info("Setting up IPython web notebook for user: %s" % user)
        user_cert = posixpath.join(profile_dir, '%s.pem' % user)
        ssl_cert = posixpath.join(profile_dir, '%s.pem' % user)
        if not node.ssh.isfile(user_cert):
            log.info("Creating SSL certificate for user %s" % user)
            ssl_subj = "/C=US/ST=SC/L=STAR/O=Dis/CN=%s" % node.dns_name
            node.ssh.execute(
                "openssl req -new -newkey rsa:4096 -days 365 "
                '-nodes -x509 -subj %s -keyout %s -out %s' %
                (ssl_subj, ssl_cert, ssl_cert))
            log.info("DONE")
        else:
            log.info("Using existing SSL certificate...")
        f = node.ssh.remote_file('%s/ipython_notebook_config.py' %
                                   profile_dir)
        notebook_port = 8888
        notebook_passwd = 'rc' + user
        sha1py = 'from IPython.lib import passwd; print passwd("%s")'
        sha1cmd = "python -c '%s'" % sha1py
        sha1pass = node.ssh.execute(sha1cmd % notebook_passwd)[0]
        f.write('\n'.join([
            "c = get_config()",
            "c.IPKernelApp.pylab = 'inline'",
            "c.NotebookApp.certfile = u'%s'" % ssl_cert,
            "c.NotebookApp.ip = '*'",
            "c.NotebookApp.open_browser = False",
            "c.NotebookApp.password = u'%s'" % sha1pass,
            "c.NotebookApp.port = %d" % notebook_port,
            "c.NotebookApp.trust_xheaders = True"
            #"c.NotebookApp.base_project_url = '/notebook/'",
            # "c.NotebookApp.base_kernel_url = '/notebook/'",
            # "c.NotebookApp.webapp_settings = {'static_url_prefix':'/notebook/static/'}"
        ]))
        f.close()

        if notebook_directory is not None:
            if not node.ssh.path_exists(notebook_directory):
                node.ssh.makedirs(notebook_directory)
            node.ssh.execute_async(
                "ipython notebook --no-browser --notebook-dir='%s'"
                % notebook_directory)
        else:
            node.ssh.execute_async("ipython notebook --no-browser")

        self._authorize_port(node, notebook_port, 'notebook')
        self._authorize_port(node, 443, 'https')
        self._nginx_conf(node, user, ssl_cert)

        url = 'https://{0}'.format(node.dns_name)
        urlport = 'https://{0}:{1}'.format(node.dns_name, notebook_port)
        log.info('IPython notebook URL:     %s'% (url))
        log.info('The notebook password is: %s'% (notebook_passwd))
        #tunnel = 'ssh -i {2} -L 2000:localhost:8888  -f -N {0}@{1}'
        #tunnel = tunnel.format(user,node.dns_name, user+'.rsa')
        self._data[user] = {'password': notebook_passwd,
                            'url': url,
                            'urlport': urlport}

    def _nginx_conf(self, node, user, ssl_cert):
        node.ssh.switch_user('root')
        f = node.ssh.remote_file('/etc/nginx/conf.d/default.conf', 'w')
        tmp = nginx_template.render({'ssl_cert': ssl_cert})
        f.write(tmp)
        f.close()
        node.ssh.execute('service nginx restart')
        node.ssh.switch_user(user)

    def _authorize_port(self, node, port, service_name, protocol='tcp'):
        group = node.cluster_groups[0]
        world_cidr = '0.0.0.0/0'
        if isinstance(port, tuple):
            port_min, port_max = port
        else:
            port_min, port_max = port, port
        port_open = node.ec2.has_permission(group, protocol, port_min,
                                            port_max, world_cidr)
        if not port_open:
            log.info("Authorizing tcp ports [%s-%s] on %s for: %s" %
                     (port_min, port_max, world_cidr, service_name))
            node.ec2.conn.authorize_security_group(
                group_id=group.id, ip_protocol='tcp', from_port=port_min,
                to_port=port_max, cidr_ip=world_cidr)
