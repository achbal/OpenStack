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

def nova_servers_create(instance_id):
    """
    Booting an instance from an image and checking status
    """
    instance_name = "{0}-qserv-{1}".format(creds['username'], instance_id)
    logging.info("Launch an instance {}".format(instance_name))

    fic = open("cloud-config.txt", "r")
    userdata = fic.read()

    # Launch an instance from an image
    instance = nova.servers.create(name=instance_name, image=image,
            flavor=flavor, userdata=userdata, key_name=key)
    # Poll at 5 second intervals, until the status is no longer 'BUILD'
    status = instance.status
    while status == 'BUILD':
        time.sleep(5)
        instance = nova.servers.get(instance.id)
        status = instance.status
    logging.info ("status: {}".format(status))
    logging.info ("Instance {} is active".format(instance_name))
    print "======================================"
    fic.close()

    return instance

def manage_ssh_key():
    """
    Manage ssh key
    """
    logging.info('Manage ssh keys')
    if nova.keypairs.findall(name=key):
        logging.debug('Remove previous ssh keys')
        nova.keypairs.delete(key=key)

    with open(os.path.expanduser('~/.ssh/id_rsa.pub')) as fpubkey:
        nova.keypairs.create(name=key, public_key=fpubkey.read())

def get_floating_ip():
    """
    Get a floating ip
    """
    i=0
    floating_ips = nova.floating_ips.list()
    floating_ip = None
    floating_ip_pool = nova.floating_ip_pools.list()[0].name

    # Check for available public ip in project
    while i<len(floating_ips) and floating_ip is None:
        if floating_ips[i].instance_id is None:
            floating_ip=floating_ips[i]
            logging.debug('Available floating ip found {}'.format(floating_ip))
        i+=1

    # Check for available public ip in ext-net pool
    if floating_ip is None:
        try:
            logging.debug("Use floating ip pool: {}".format(floating_ip_pool))
            floating_ip = nova.floating_ips.create(floating_ip_pool)
        except novaclient.exceptions.Forbidden as e:
            logging.fatal("Unable to retrieve public IP: {0}".format(e))
            sys.exit(1)

    return floating_ip

def terminate_instance(vm_name):
    """
    Retrieve an instance by name and shut it down
    """
    server = nova.servers.find(name=vm_name)
    server.delete()


if __name__ == "__main__":
    try:
        VERSION=2.4
        logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)

        # Disable warnings
        warnings.filterwarnings("ignore")

        creds = get_nova_creds()
        nova = client.Client(VERSION, **creds)

        # Find a floating ip to gateway
        floating_ip = get_floating_ip()
        if not floating_ip:
            logging.fatal("Unable to add public ip to Qserv gateway")
            sys.exit(2)
        
        # MANAGE SSH KEY
        key = "{}-qserv".format(creds['username'])
        manage_ssh_key()

        # Find an image and a flavor to launch an instance
        image = nova.images.find(name="CentOS 7")
        flavor = nova.flavors.find(name="c1.medium")

        # Create a new instance as GW and add floating_ip to it
        gateway_id=0
        gateway_instance = nova_servers_create(gateway_id)
        logging.info("Add floating ip({}) to gateway".format(floating_ip))
        gateway_instance.add_floating_ip(floating_ip)
        
        # Create instances as workers
        for instance_id in range(1,3):
            worker_instance = nova_servers_create(instance_id)

    except Exception as exc:
        logging.critical('Exception occured: %s', exc, exc_info=True)
        sys.exit(3)
