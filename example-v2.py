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

def create_instance(instance_id):
    """
    Booting an instance from an image and checking status
    """
    instance_name = "{0}-qserv-{1}".format(creds['username'], instance_id)
    logging.info("Launch an instance {}".format(instance_name))
    # Launch an instance from an iamge
    instance = nova.servers.create(name=instance_name, image=image, flavor=flavor, key_name=key)
    # Poll at 5 second intervals, until the status is no longer 'BUILD'
    status = instance.status
    while status == 'BUILD':
        time.sleep(5)
        instance = nova.servers.get(instance.id)
        status = instance.status
    logging.info ("status: {}".format(status))
    logging.info ("Instance {} is active".format(instance_name))
    print "======================================"

    return instance

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
    i=0
    # Check for available public ip in project
    floating_ips = nova.floating_ips.list()
    is_available = False
    floating_ip = None

    logging.debug('iXXXXXXXXXXXXXXX Avaible floating ip found {}'.format(floating_ip))
    while i<len(floating_ips) and not is_available:
        if floating_ips[i].instance_id is None:
            floating_ip=floating_ips[i]
            is_available=True
            logging.debug('Avaible floating ip found {}'.format(floating_ip))
        i+=1

    return floating_ip

def add_floating_ip_GW(floating_ip,gateway_id):
    #logging.info("create a floating ip adress {}".format(floating_ip))
    instance = nova.servers.find(name="{0}-qserv-{1}".format(creds['username'], gateway_id))
    instance.add_floating_ip(floating_ip)

def terminate_instance(vm_name):
    """
    Retrieve an instance by name and shut it down
    """	
    server = nova.servers.find(name=vm_name)
    server.delete()

def change_sec_grp():
    """
    Allow port 22 and ICMP in the default security group
    """  
    secgroup = nova.security_groups.find(name="default")
    nova.security_group_rules.create(secgroup.id, ip_protocol="tcp", from_port=22, to_port=22)
    nova.security_group_rules.create(secgroup.id, ip_protocol="icmp", from_port=-1, to_port=-1)


if __name__ == "__main__":
    try:
        VERSION=2.4
        
        logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
        # Disable warnings
        warnings.filterwarnings("ignore")
        
        creds = get_nova_creds()
        nova = client.Client(VERSION, **creds)
        # MANAGE SSH KEY
        key = "{}-qserv".format(creds['username'])
        manage_ssh_key()
        # Find an image and a flavor to launch an instance
        image = nova.images.find(name="CentOS 7")
        flavor = nova.flavors.find(name="c1.medium")
        # net = nova.networks.find(label="public")
        # nics = [{'079bde3e-af21-4b9b-a934-b3286fdc9d07': net.id}]
 
        # Boot a new instance as GW
        gateway_id=0
        instance = create_instance(gateway_id)
        # Boot instances as workers
        #for i in range(1,3):
        #    create_instance(i)
        # Get floating ip and add it to gateway
        floating_ip = get_floating_ip()

	if floating_ip:
            add_floating_ip_GW(floating_ip,gateway_id)

    except Exception as exc:
        logging.critical('Exception occured: %s', exc, exc_info=True)
        sys.exit(1)

