import logging 
import os

from keystoneauth1 import loading
from keystoneauth1 import session
from novaclient import client

VERSION=2.4

def get_nova_creds():
    d = {}
    d['username'] = os.environ['OS_USERNAME']
    d['password'] = os.environ['OS_PASSWORD']
    d['auth_url'] = os.environ['OS_AUTH_URL']
    d['project_id'] = os.environ['OS_TENANT_NAME']
    logging.debug('Openstack user: %s' % d['username'])
    return d

creds = get_nova_creds()

loader = loading.get_plugin_loader('password')
auth = loader.load_from_options(**creds)
sess = session.Session(auth=auth)
nova = client.Client(VERSION, session=sess)
