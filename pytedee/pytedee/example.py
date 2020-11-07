'''
Created on 01.11.2020

@author: joerg
'''
import time
from pytedee.TedeeClient import TedeeClient
from pytedee.Lock import Lock
from pytedee.TedeeClientException import TedeeClientException

'''Tedee Credentials'''
username = "username"
password = "password"

client = TedeeClient(username, password)
locks = client.get_locks()
for lock in locks:
    print(lock.get_name())
    client.unlock(lock.get_id())
    time.sleep(3)
    client.open(lock.get_id())
    print("is_locked: " + str(client.is_locked(lock.get_id())))
    print("is_unlocked: " + str(client.is_unlocked(lock.get_id())))
    print(client.get_battery(lock.get_id()))
