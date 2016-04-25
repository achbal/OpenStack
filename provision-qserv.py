import logging 
import os
import warnings
from novaclient import client

VERSION=2.4

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

warnings.filterwarnings("ignore")

def get_nova_creds():
    d = {}
    d['username'] = os.environ['OS_USERNAME']
    d['api_key'] = os.environ['OS_PASSWORD']
    d['auth_url'] = os.environ['OS_AUTH_URL']
    d['project_id'] = os.environ['OS_TENANT_NAME']
    d['insecure'] = True
    logging.debug('Openstack user: %s' % d['username'])
    return d

creds = get_nova_creds()

nova = client.Client(VERSION, **creds)

# MANAGE SSH KEY
key = creds['username']+"-qserv"
logging.info('Manage ssh keys')
if nova.keypairs.findall(name=key):
    logging.debug('Remove previous ssh keys')
    nova.keypairs.delete(key=key)

with open(os.path.expanduser('~/.ssh/id_rsa.pub')) as fpubkey:
    nova.keypairs.create(name=key, public_key=fpubkey.read())


# LAUNCH AN INSTANCE FROM AN IMAGE
logging.info("Launching instance")
instance_id=0
instance_name = "{0}-qserv-{1}".format(creds['username'], instance_id)
image = nova.images.find(name="CentOS 7")
flavor = nova.flavors.find(name="c1.medium")
instance = nova.servers.create(name=instance_name, image=image, flavor=flavor, key_name=key)

logging.info("SUCCESS")
