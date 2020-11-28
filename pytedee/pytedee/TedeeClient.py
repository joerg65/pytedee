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

    
class TedeeClient(object):
    '''Classdocs'''

    def __init__(self, username, password, timeout=TIMEOUT):
        '''Constructor'''
        self._available = False
        self._username = username
        self._password = password
        self._token = None
        self._sensor_list = []
        self._timeout = timeout
        self._lock_id = None
        self._token_valid_until = datetime.datetime.now()
        
        self.get_token()
        
        if (self.is_token_valid() == True):
            self.get_devices()

    def get_token(self, **kwargs):
        self._have_token = False
        auth_parameters["username"] = self._username
        auth_parameters["password"] = self._password
        self._token = None
        r = requests.post(auth_url, params=auth_parameters, headers=auth_header,
            timeout=self._timeout)
        try:
            self._token = r.json()["access_token"]
            #_LOGGER.error("result: %s", r.json())
            _LOGGER.debug("Got new token.")
        except KeyError:
            raise TedeeClientException("Authentication not successfull")
        
        '''Create the api header with new token'''
        self._api_header = {"Content-Type": "application/json", "Authorization": "Bearer " + self._token}
        
        '''Store the date when actual token expires'''
        expires = int(r.json()["expires_in"])
        
        self._token_valid_until = datetime.datetime.now() + datetime.timedelta(seconds=expires)
        _LOGGER.debug("Token valid until: %s", self._token_valid_until)
        
    def get_devices(self):
        '''Get the list of registered locks'''
        api_url_lock = "https://api.tedee.com/api/v1.15/my/lock"
        r = requests.get(api_url_lock, headers=self._api_header,
            timeout=self._timeout)
        _LOGGER.debug("Locks %s", r.json())
        result = r.json()["result"]

        for x in result:            
            id = x["id"]
            name = x["name"]
            isConnected = x["isConnected"]
            state = x["lockProperties"]["state"]
            batteryLevel = x["lockProperties"]["batteryLevel"]
            isCharging = x["lockProperties"]["isCharging"]
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
        payload = {"deviceId":id}

        if (self.ensure_token_is_valid() == True):
            r = requests.post(api_url_open, headers=self._api_header, data=json.dumps(payload),
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
        payload = {"deviceId":id}

        if (self.ensure_token_is_valid() == True):
            r = requests.post(api_url_close, headers=self._api_header, data=json.dumps(payload),
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
        payload = {"deviceId":id}

        if (self.ensure_token_is_valid() == True):
            r = requests.post(api_url_pull, headers=self._api_header, data=json.dumps(payload),
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
        payload = {"deviceId":id}
        
        api_url_battery = "https://api.tedee.com/api/v1.15/my/device/" + str(id) + "/battery"
        r = requests.get(api_url_battery, headers=self._api_header,
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
        api_url_state = "https://api.tedee.com/api/v1.15/my/lock/sync"
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
                        _LOGGER.debug("Id: %s, State: %d, battery: %d", state["id"], lockProperties ["state"], lockProperties["batteryLevel"])
                        battery_level = lockProperties["batteryLevel"]
                        lock.set_battery_level(battery_level)
                        '''Todo: do something with state'''
                        lock.set_state(lockProperties["state"])
                        break
        except KeyError:
            _LOGGER.error("result: %s", r.json())
            
    def is_token_valid(self):
        return self._token_valid_until > datetime.datetime.now()

    def ensure_token_is_valid(self):
        if (self.is_token_valid() == False):
            self.get_token()
        return self.is_token_valid() == True

    def find_lock(self, id):
        for lock in self._sensor_list:
            if id == lock.get_id():
                return lock
        raise TedeeClientException("This Id not found")
                      
    def update(self, id):
        if (self.is_token_valid() == False):
            _LOGGER.debug("Need new token...")
            self.get_token()
        if (self.is_token_valid() == True):
            self.get_state()
            return self.get_battery(id)
        else:
            return False
    
auth_url = "https://tedee.b2clogin.com/tedee.onmicrosoft.com/B2C_1_SignIn_Ropc/oauth2/v2.0/token"
auth_parameters = {
    "grant_type": "password",
    "scope": "openid 02106b82-0524-4fd3-ac57-af774f340979",
    "client_id": "02106b82-0524-4fd3-ac57-af774f340979",
    "response_type": "token" }
auth_header = {"Content-Type": "application/x-www-form-urlencoded"}
api_url_devices = "https://api.tedee.com/api/v1.15/my/device"
api_url_open = "https://api.tedee.com/api/v1.15/my/lock/open"
api_url_close = "https://api.tedee.com/api/v1.15/my/lock/close"
api_url_pull = "https://api.tedee.com/api/v1.15/my/lock/pull-spring"


root = logging.getLogger()
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("pytedee").setLevel(logging.WARNING)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
root.addHandler(handler)
