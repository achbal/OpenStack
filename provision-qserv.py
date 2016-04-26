#!/usr/bin/env python

import logging
from novaclient import client
import novaclient.exceptions
import os
from Crypto.PublicKey import RSA
import sys 
import tempfile
import time

VERSION=2.4
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

# TODO create function:
# examples: 
# ~/src/qserv/admin/bin/qserv-data-loader.py


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

key = creds['username']+"-qserv"

# CREATE SSH KEY PAIR HERE
mykey = RSA.generate(2048, os.urandom)
mykey.exportKey('OpenSSH')

# PUT IT IN TEMP FILE IN ~/.ssh/
sshKeyPair = tempfile.mktemp(suffix='', prefix='tmp', dir=None)

# MANAGE SSH KEY
logging.info('Manage ssh keys')
if nova.keypairs.findall(name=key):
    logging.debug('Remove previous ssh keys')
    nova.keypairs.delete(key=key)

with open(os.path.expanduser('~/.ssh/id_rsa.pub')) as fpubkey:
    nova.keypairs.create(name=key, public_key=fpubkey.read())

# LAUNCH AN INSTANCE FROM AN IMAGE
image = nova.images.find(name="CentOS 7")
flavor = nova.flavors.find(name="c1.medium")
#net = nova.networks.find(label="public")
#nics = [{'079bde3e-af21-4b9b-a934-b3286fdc9d07': net.id}]

for i in range(1,3):
    img_name = creds['username']+"-qserv-"+str(i)
    logging.info("Create image %s" % img_name)
    instance = nova.servers.create(name=img_name, image=image, flavor=flavor, key_name=key)
    print "XXXXXXXXXXXXXXXXXXXXX: %s" % instance
    # Poll at 5 second intervals, until the status is no longer 'BUILD'
    status = instance.status
    while status == 'BUILD':
        time.sleep(5)
        instance = nova.servers.get(instance.id)
        status = instance.status
    logging.info ("status: %s" % status)
    logging.info ("image %s is active" % img_name)


# GET FLOATING IP AND ADD IT TO GW

# Check for available public ip in project
for ip in nova.floating_ips.list():
    print "ip: {0}, instance_id: {1} ".format(ip.ip, ip.instance_id)

# Check for available public ip in ext-net pool
floating_ip_pool = nova.floating_ip_pools.list()[0].name
logging.debug('Use floating ip pool:%s' % floating_ip_pool)
try:
    floating_ip = nova.floating_ips.create(floating_ip_pool)
except novaclient.exceptions.Forbidden as e:
    logging.fatal("Unable to retrieve public IP: {0}".format(e))
    sys.exit(1)

logging.info("create a floating ip adress {}".format(floating_ip))
instance = nova.servers.find(name=creds['username']+"-qserv-0")
instance.add_floating_ip(floating_ip)

logging.info("Execution Completed")
