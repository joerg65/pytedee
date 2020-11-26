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
print ("Token: " + str(client._token))
print ("Token valid: " + str(client._token_valid_until))
locks = client.get_locks()
for lock in locks:
    print("----------------------------------------------")
    print("Lock name: " + lock.get_name())
    print("Lock id: " + str(lock.get_id()))
    print("Lock Battery: " + str(lock.get_battery_level()))
    client.get_state()
    print("Is Locked: " + str(client.is_locked(lock.get_id())))
    print("Is Unlocked: " + str(client.is_unlocked(lock.get_id())))
#    client.unlock(lock.get_id())
#    time.sleep(3)
#    client.open(lock.get_id())
