#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov 29 14:58:39 2021

This script updates the IP addresses stored in mongodb and updates the host file of every host that execute it

@author: mw
"""
import constants
import urllib.parse
from pymongo import MongoClient
# pprint library is used to make the output look more pretty
from pprint import pprint
from netifaces import interfaces, ifaddresses, AF_INET

from pathlib import Path
import socket


from python_hosts import Hosts, HostsEntry

import subprocess
""" 

 """
def check_file():
    try:
        
        file = Path('/opt/ipcheck/ip.txt')
        file.touch(exist_ok=True)
        f = open(file, "r")
        return(f.read())
    
    except Exception as e:
        print(str(e)+"<--")
    
    finally:
        f.close()
        
def update_file(ip_in_file, current_ip):
    print("{0}, current: {1}".format(ip_in_file, current_ip))
    if ip_in_file != current_ip:
        file = open('/opt/ipcheck/ip.txt', "w")
        file.write(current_ip)
        return(current_ip)

def save_into_mongodb(ipAddr):
    user_name = constants.mdb_user
    pass_word = constants.mdb_pwd
    
    client = MongoClient(f"mongodb+srv://{user_name}:{urllib.parse.quote_plus(pass_word)}@tools.vlo1p.mongodb.net/linuxUtils?retryWrites=true&w=majority")
    
    query = {"client":socket.gethostname()}
    update = {'$set':{"ip":ipAddr}}
    #Set DB name
    db=client.linuxUtils
    #update
    db.vpnClients.update_one(query, update, upsert=True)
    

def get_ip():
    interfacesList = interfaces()
    for interface in interfacesList:
        addresses = ifaddresses(interface)
        #print(addresses)
        for instance in addresses:
            if constants.ip_prefix in addresses[instance][0]["addr"]:
                return(addresses[instance][0]["addr"])
                 
                
def updateHosts(hostname, addr):
    hosts = Hosts(path='/home/mw/Public/hosts')
    new_entry = HostsEntry(entry_type='ipv4', address=addr, names=[hostname])
    hosts.add([new_entry], force=True)
    hosts.write()
    
def get_hosts_from_mdb():
    user_name = constants.mdb_user
    pass_word = constants.mdb_pwd  
    
    client = MongoClient(f"mongodb+srv://{user_name}:{urllib.parse.quote_plus(pass_word)}@tools.vlo1p.mongodb.net/linuxUtils?retryWrites=true&w=majority")
    mydb = client["linuxUtils"]
    mycol = mydb["vpnClients"]

    for host_ip in mycol.find({'client':{'$ne':socket.gethostname()}},{'_id':0, 'client':1,'ip':1}):
        #print(host_ip)
        updateHosts(host_ip['client'], host_ip['ip']) 
        remove_old_sshkey(host_ip['client'])
        
def remove_old_sshkey(hostname):
    'ssh-keygen -f "/home/mw/.ssh/known_hosts" -R "tulrpi"   '
    
    subprocess.run(['ssh-keygen', '-f', "/home/mw/.ssh/known_hosts", '-R', hostname],
                   capture_output=True,
                   input="yes\n", 
                   text=True)
    
      
if __name__ == '__main__':
    ip_in_file = check_file()
    current_ip = get_ip()
    result = update_file(ip_in_file, current_ip)
    if result is not None:
        save_into_mongodb(result)
    get_hosts_from_mdb()
