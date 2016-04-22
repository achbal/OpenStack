#!/usr/bin/env python

import keystoneclient.v3.credentials 
import logging
import novaclient.v1_1.client as nvclient
import os,sys
import time

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)

def get_nova_creds():
    d = {}
    d['username'] = os.environ['OS_USERNAME']
    d['api_key'] = os.environ['OS_PASSWORD']
    d['auth_url'] = os.environ['OS_AUTH_URL']
    d['project_id'] = os.environ['OS_TENANT_NAME']
    logging.debug('Openstack user: %s' % d['username'])
    return d

creds = get_nova_creds()
nova = nvclient.Client(**creds)

logging.info('Manage ssh keys')

if nova.keypairs.findall(name="achbal"):
    logging.debug('Remove previous ssh keys')
    nova.keypairs.delete(key="achbal")

with open(os.path.expanduser('~/.ssh/achbal-id_rsa.pub')) as fpubkey:
    nova.keypairs.create(name="achbal", public_key=fpubkey.read())
image = nova.images.find(name="CentOS 7")
flavor = nova.flavors.find(name="c1.medium")
#net = nova.networks.find(label="public")
#nics = [{'079bde3e-af21-4b9b-a934-b3286fdc9d07': net.id}]

for i in range(0,2):
    logging.info("Create VM%02d" % i)
    NAMEIMG = creds['username']+"-qserv-"+str(i) 
    KEY = "achbal"
     print "XXXXXXXXXXXXXXXXXXXX %s" %NAMEIMG 
     sys.exit(0)
    instance = nova.servers.create(name=NAMEIMG, image=image, flavor=flavor, key_name=KEY)
    # Poll at 5 second intervals, until the status is no longer 'BUILD'
    status = instance.status
    while status == 'BUILD':
        time.sleep(5)
        # Retrieve the instance again so the status field updates
        instance = nova.servers.get(instance.id)
        status = instance.status
    logging.info ("status: %s" % status)
    logging.info ("VM%02d is active"% i)
logging.info("Execution Completed")
