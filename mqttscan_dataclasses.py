from dataclasses import dataclass, field
from multiprocessing import Process, Queue
from asyncio import Task
from collections import OrderedDict
from operator import itemgetter 

# ==================================================================================
@dataclass
class tasmotaItem:
    # STATUS5
    hostname: str = ''
    ipaddress: str = ''
    mac: str = ''
    # STATUS6
    mqtthost: str = ''
    mqttport: int = 0
    mqttuser: str = ''
    mqttclient: str = ''
    fbtopic: str = ''
    # STATUS2
    version: str = ''
    builddate: str = ''
    core: str = ''
    # STATUS1
    otaurl: str = ''
    restartreason: str = ''
    uptime: str = ''
    startuputc: str = ''
    # STATUS11
    wifi_ssid: str = ''
    wifi_bssid: str = ''
    wifi_ch: int = 0
    wifi_rssi: int = 0
    # OTHERS
    fulltopic: str = ''
    grouptopic: str = ''
    # STATUS
    module: int = 0
    topic: str = ''
    friendlyname: list = field(default_factory=list)
    # STATUS 4
    features: list = field(default_factory=list)

    def __lt__(self, other):
      return self.ipaddress < other.ipaddress

# ----------------------------------------------------------------------------------
@dataclass
class tasmotaDict:
  item: {tasmotaItem} = field(default_factory=dict)

  def add(self, key, item: tasmotaItem):
    self.item[key] = item
    return item

  def get(self, key) -> tasmotaItem:
    if key in self.item:
      return self.item[key]
    return None

  def delete(self, key):
    if key in self.item:
      del self.item[key]
      return True
    return False

  def clear(self):
      self.item.clear()

  def items(self):
      return self.item.items()
  
  def sort(self):
      return OrderedDict(sorted(self.item.items(), key=itemgetter(1), reverse=False))

# ==================================================================================
@dataclass
class shelliesItem:
    mac: str = ''
    ipaddress: str = ''
    fw: str = ''
    new_fw: bool = False
    shelly_type: str = ''
    # HTTP
    device_type: str = ''
    hostname: str = ''
    mqtt: bool = False
    mqtthost: str = ''
    mqttuser: str = ''
    wifi_ssid: str = ''
    sntp_server: str = ''
    tz: str = ''
    tz_autodetect: bool = False

    def __lt__(self, other):
      return self.ipaddress < other.ipaddress

# ----------------------------------------------------------------------------------
@dataclass
class shelliesDict:
  item: {shelliesItem} = field(default_factory=dict)

  def add(self, key, item: shelliesItem):
    self.item[key] = item
    return item

  def get(self, key) -> shelliesItem:
    if key in self.item:
      return self.item[key]
    return None

  def delete(self, key):
    if key in self.item:
      del self.item[key]
      return True
    return False

  def clear(self):
      self.item.clear()

  def items(self):
      return self.item.items()

  def sort(self):
      return OrderedDict(sorted(self.item.items(), key=itemgetter(1), reverse=False))
