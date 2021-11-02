'''
Created on 01.11.2020

@author: joerg.wolff@gmx.de
'''
import json
import logging
import requests
import sys
import datetime
from threading import Timer

try:
    from .Lock import Lock
    from .TedeeClientException import TedeeClientException
except:
    from Lock import Lock
    from TedeeClientException import TedeeClientException

_LOGGER = logging.getLogger(__name__)

TIMEOUT = 10
LOCK_ID = '#lockid#'
    
class TedeeClient(object):
    '''Classdocs'''

    def __init__(self, personalToken, timeout=TIMEOUT):
        '''Constructor'''
        self._available = False
        self._personalToken = personalToken
        self._sensor_list = []
        self._timeout = timeout
        self._lock_id = None

        '''Create the api header with new token'''
        self._api_header = {"Content-Type": "application/json", "Authorization": "PersonalKey " + self._personalToken}
        
        self.get_devices()

    def get_devices(self):
        '''Get the list of registered locks'''
        api_url_lock = api_url_base+"my/lock"
        r = requests.get(api_url_lock, headers=self._api_header,
            timeout=self._timeout)
        _LOGGER.debug("Locks %s", r.json())
        result = r.json()["result"]

        for x in result:            
            id = x["id"]
            name = x["name"]
            isConnected = x["isConnected"]
            state = self.assign_null_or_lock_state(x["lockProperties"])
            batteryLevel = self.assign_null_or_lock_batteryLevel(x["lockProperties"])
            isCharging = self.assign_null_or_lock_isCharging(x["lockProperties"])
            isEnabledPullSpring =x["deviceSettings"]["pullSpringEnabled"]
            durationPullSpring =x["deviceSettings"]["pullSpringDuration"]
            
            lock = Lock(name, id)
            lock.set_connected(isConnected)
            lock.set_state(state)
            lock.set_battery_level(batteryLevel)
            lock.set_is_charging(isCharging)
            lock.set_is_enabled_pullspring(isEnabledPullSpring)
            lock.set_duration_pullspring(durationPullSpring)
            
            self._lock_id = id
            '''store the found lock in _sensor_list and get the battery_level'''

            self._sensor_list.append(lock)

        if self._lock_id == None:
            raise TedeeClientException("No lock found")
    
    def get_locks(self):
        '''Return a list of locks'''
        return self._sensor_list
    
    def unlock(self, id):
        '''Unlock method'''
        lock = self.find_lock(id)

        r = requests.post(api_url_open.replace(LOCK_ID, str(id)), headers=self._api_header,
        timeout=self._timeout)
        
        success = r.json()["success"]
        if success:
            lock.set_state(2)
            _LOGGER.debug("unlock command successful, id: %d ", id)
        
            t = Timer(2, self.get_state)
            t.start()
            
    def lock(self, id):
        ''''Lock method'''
        lock = self.find_lock(id)

        r = requests.post(api_url_close.replace(LOCK_ID, str(id)), headers=self._api_header,
        timeout=self._timeout)
        
        success = r.json()["success"]
        if success:
            lock.set_state(6)
            _LOGGER.debug("lock command successful, id: %d ", id)
            
            t = Timer(2, self.get_state)
            t.start()
        
    def open(self, id):
        '''Open the door latch'''
        lock = self.find_lock(id)

        r = requests.post(api_url_pull.replace(LOCK_ID, str(id)), headers=self._api_header,
        timeout=self._timeout)

        success = r.json()["success"]
        if success:
            lock.set_state(2)
            _LOGGER.debug("open command successful, id: %d ", id)

            t = Timer(lock.get_duration_pullspring() + 1, self.get_state)
            t.start()
                
    def is_unlocked(self, id):
        lock = self.find_lock(id)
        return lock.get_state() == 2
    
    def is_locked(self, id):
        lock = self.find_lock(id)
        return lock.get_state() == 6
    
    def get_battery(self, id):
        lock = self.find_lock(id)
        
        r = requests.get(api_url_battery.replace(LOCK_ID, str(id)), headers=self._api_header,
            timeout=self._timeout)
        _LOGGER.debug("result: %s", r.json())
        result = r.json()["result"]
        try:
            success = r.json()["success"]
            if success:
                for lock in self._sensor_list:
                    if id == lock.get_id():
                        lock.set_battery_level(result["level"])
                        _LOGGER.debug("id: %d, battery level: %d", id, lock.get_battery_level())
            return success
        except KeyError:
            _LOGGER.error("result: %s", r.json())
            return False
            
    def get_state(self):
        r = requests.get(api_url_state, headers=self._api_header)
        states = r.json()["result"]
        try:
            for state in states:
                id = state["id"]
                is_connected = state["isConnected"]
                for lock in self._sensor_list:
                    if id == lock.get_id():
                        lock.set_connected(is_connected)
                        lockProperties = state["lockProperties"]
                        lock_state = self.assign_null_or_lock_state(lockProperties)
                        lock_batteryLevel = self.assign_null_or_lock_state(lockProperties)
                        lock_isCharging = self.assign_null_or_lock_isCharging(lockProperties)
                        _LOGGER.debug("Id: %s, State: %d, battery: %d", lock_state, lock_isCharging, lock_batteryLevel)

                        lock.set_battery_level(lock_batteryLevel)
                        '''Todo: do something with state'''
                        lock.set_state(lock_state)
                        break
        except KeyError:
            _LOGGER.error("result: %s", r.json())
            
    def find_lock(self, id):
        for lock in self._sensor_list:
            if id == lock.get_id():
                return lock
        raise TedeeClientException("This Id not found")

    def assign_null_or_lock_state(self, value):
        if (value == None):
            return None;                  
        else:
            return value["state"]
    
    def assign_null_or_lock_batteryLevel(self, value):
        if (value == None):
            return None;                  
        else:
            return value["batteryLevel"]

    def assign_null_or_lock_isCharging(self, value):
        if (value == None):
            return None;                  
        else:
            return value["isCharging"]            

api_url_base = "https://t01-nofo-api.azurewebsites.net/api/v1.22/"
api_url_devices = api_url_base+"my/device"
api_url_open = api_url_base+"my/lock/"+LOCK_ID+"/operation/lock"
api_url_close = api_url_base+"my/lock/"+LOCK_ID+"/operation/unlock"
api_url_pull = api_url_base+"my/lock/"+LOCK_ID+"/operation/pull"
api_url_battery = api_url_base+"my/device/"+LOCK_ID+"/battery"
api_url_state = api_url_base+"my/lock/sync"

root = logging.getLogger()
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("pytedee").setLevel(logging.WARNING)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
root.addHandler(handler)
