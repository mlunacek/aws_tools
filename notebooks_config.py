#!/usr/bin/env python
import os
import socket
import subprocess
from IPython.lib import passwd

import jinja2 as jin

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

# Kill all notebooks
pid = subprocess.Popen('pkill ipython', shell=True)
pid.wait()

# Remove profile
pid = subprocess.Popen('rm -rf ~/.ipython/profile_default', shell=True)
pid.wait()

# Create profile
pid = subprocess.Popen('ipython profile create', shell=True)
pid.wait()

# Create ssl cert
user = os.environ['USER']
home = os.environ['HOME']
host = socket.gethostname()

profile_dir = os.path.join(home,'.ipython/profile_default')

user_cert = os.path.join(profile_dir, '%s.pem' % user)
ssl_cert = os.path.join(profile_dir, '%s.pem' % user)
ssl_subj = "/C=US/ST=SC/L=STAR/O=Dis/CN={0}".format(host)
cmd = 'openssl req -new -newkey rsa:4096 -days 365 -nodes -x509 -subj {0} -keyout {1} -out {2}'
cmd = cmd.format(ssl_subj, ssl_cert, ssl_cert)

pid = subprocess.Popen(cmd, shell=True)
pid.wait()

notebook_port = 8888
notebook_passwd = 'rc' + user
sha1pass = passwd(notebook_passwd)

# Modify config
with open(os.path.join(profile_dir,'ipython_notebook_config.py'), 'w') as outfile:
	outfile.write('\n'.join([
            "c = get_config()",
            "c.IPKernelApp.pylab = 'inline'",
            "c.NotebookApp.certfile = u'%s'" % ssl_cert,
            "c.NotebookApp.ip = '*'",
            "c.NotebookApp.open_browser = False",
            "c.NotebookApp.password = u'%s'" % sha1pass,
            "c.NotebookApp.port = %d" % notebook_port,
            "c.NotebookApp.trust_xheaders = True"]))


# NGINX
tmp = nginx_template.render({'ssl_cert': ssl_cert})
with open(os.path.join(home,'tmp.conf'), 'w') as outfile:
	outfile.write(tmp)

# cp /home/molu8455/tmp.conf /etc/nginx/conf.d/default.conf; service nginx restart
# ssh node001 `cp /home/user001/tmp.conf /etc/nginx/conf.d/default.conf; service nginx restart`

















