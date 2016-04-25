#!/usr/bin/env python

"""
@author  Oualid Achbal, ISIMA student , IN2P3

"""

# -------------------------------
#  Imports of standard modules --
# -------------------------------
import logging
import os
import sys
import time
import warnings

# ----------------------------
# Imports for other modules --
# ----------------------------
from novaclient import client
import novaclient.exceptions

VERSION=2.4

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

# Disable warnings 
warnings.filterwarnings("ignore")

# -----------------------
# Exported definitions --
# -----------------------
def get_nova_creds():
    """
    Extract the login information from the environment
    """
    d = {}
    d['username'] = os.environ['OS_USERNAME']
    d['api_key'] = os.environ['OS_PASSWORD']
    d['auth_url'] = os.environ['OS_AUTH_URL']
    d['project_id'] = os.environ['OS_TENANT_NAME']
    d['insecure'] = True
    logging.debug("Openstack user: {}".format(d['username']))
    return d

def boot_image(instance_id):
    """
    Booting an instance and checking status 
    """
    instance_name = "{0}-qserv-{1}".format(creds['username'], instance_id)
    logging.info("Launch an instance {}".format(instance_name))
    instance = nova.servers.create(name=instance_name, image=image, flavor=flavor, key_name=key)
    # Poll at 5 second intervals, until the status is no longer 'BUILD'
    status = instance.status
    while status == 'BUILD':
        time.sleep(5)
        instance = nova.servers.get(instance.id)
        status = instance.status
    logging.info ("status: {}".format(status))
    logging.info ("Instance {} is active".format(instance_name))
    print("======================================")

def manage_ssh_key():
    """
    Managing ssh key
    """
    logging.info('Manage ssh keys')
    if nova.keypairs.findall(name=key):
        logging.debug('Remove previous ssh keys')
        nova.keypairs.delete(key=key)

    with open(os.path.expanduser('~/.ssh/id_rsa.pub')) as fpubkey:
        nova.keypairs.create(name=key, public_key=fpubkey.read())

def get_floating_ip():
    """
    Get floating ip and add it to GW
    """
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
    instance = nova.servers.find(name="{}-qserv-0".format(creds['username']))
    instance.add_floating_ip(floating_ip)

    logging.info("Execution Completed")


if __name__ == "__main__":
    try:
        creds = get_nova_creds()
        nova = client.Client(VERSION, **creds)
        # MANAGE SSH KEY
        key = "{}-qserv".format(creds['username'])
        # LAUNCH AN INSTANCE FROM AN IMAGE
	image = nova.images.find(name="CentOS 7")
        flavor = nova.flavors.find(name="c1.medium")
	# net = nova.networks.find(label="public")
       	# nics = [{'079bde3e-af21-4b9b-a934-b3286fdc9d07': net.id}]
	
     	# Boot instances as workers
	for i in range(1,3):
            boot_image(i)
        # Boot a new instance as GW
        boot_image(0)
        get_floating_ip()
        #sys.exit(loader.run())
    except Exception as exc:
        logging.critical('Exception occured: %s', exc, exc_info=True)
        sys.exit(1)

