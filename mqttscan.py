# coding=utf-8
# !/usr/bin/python3
# Name:         MQTT SCANNER FOR SONOFF AND SHELLY DEVICES
#
# Author:       Timo Koponen
#
# Created:      23.09.2019
# Copyright:    (c) 2019
# Licence:      MIT
# Version:      1.2.7
#
# Required:     hbmqtt                                  // pipenv install hbmqtt
#               aiohttp
# dev:          pylint                                  // pipenv install -d pylint
# -------------------------------------------------------------------------------
_PROGRAM_NAME = 'mqttscan'
_PROGRAM_PY = 'mqttscan.py'
_VERSION = '1.2.7 (191123)'

# _TASMOTA_SUB =           ['tasmota/+/stat/#', 'stat/tasmota/#']
_TASMOTA_SUB =           ['sonoff/+/stat/#', 'stat/sonoff/#', 'tasmota/+/stat/#', 'stat/tasmota/#']
_TASMOTA_PUB_PAYLOAD =   b'status ; status 1 ; status 2 ; status 4 ; status 5 ; status 6 ; status 11 ; FullTopic ;'
_TASMOTA_PUB =           [('sonoffs/cmnd/backlog', _TASMOTA_PUB_PAYLOAD), ('cmnd/sonoffs/backlog', _TASMOTA_PUB_PAYLOAD),
                         ('tasmotas/cmnd/backlog', _TASMOTA_PUB_PAYLOAD), ('cmnd/tasmotas/backlog', _TASMOTA_PUB_PAYLOAD)]
_SHELLIES_SUB =         ['shellies/announce']
_SHELLIES_PUB_PAYLOAD = b'announce'
_SHELLIES_PUB =         [('shellies/command', _SHELLIES_PUB_PAYLOAD)]

_ALL_SUB =              ['sonoff/+/stat/#', 'stat/sonoff/#', 'tasmota/+/stat/#', 'stat/tasmota/#', 'shellies/announce']
_ALL_PUB =              [('sonoffs/cmnd/backlog', _TASMOTA_PUB_PAYLOAD), ('cmnd/sonoffs/backlog', _TASMOTA_PUB_PAYLOAD),
                         ('tasmotas/cmnd/backlog', _TASMOTA_PUB_PAYLOAD), ('cmnd/tasmotas/backlog', _TASMOTA_PUB_PAYLOAD),
                         ('shellies/command', _SHELLIES_PUB_PAYLOAD)]

import os
import logging
_LOG_CFGFILE = 'logging.json'
from logger_config import logger_config
logger = None 

import sys
import ssl
import argparse
import asyncio
import aiohttp
from aiohttp.client_exceptions import ClientConnectorCertificateError, ClientConnectorError, ServerDisconnectedError, ServerTimeoutError
import platform
import uuid
import json
from datetime import datetime as _dt
from datetime import timedelta
from multiprocessing import cpu_count
from hbmqtt.client import MQTTClient, ClientException, ConnectException
from hbmqtt.mqtt.constants import QOS_0, QOS_1, QOS_2

from mqttscan_dataclasses import tasmotaItem, tasmotaDict, shelliesItem, shelliesDict

_DEFAULT_BROKER =       'mqtt://localhost:1883'
_DEFAULT_LOGCONFIG =    'logging.json'
_DEFAULT_VERBOSE =      'basic'
_DEFAULT_FEATURES =     False
_DEFAULT_MQTT_TIMEOUT = 1
_DEFAULT_HTTP_TIMEOUT = 8
_DEFAULT_QOS = QOS_0
_DEFAULT_CAFILE = 'ca.crt'
_DEFAULT_CAPATH = f'{os.path.dirname(os.path.abspath(__file__))}'


# ==============================================================================
class main_class():
    SLEEP_TIME = 1.0
    _run = True
    _tasmota_module_type = [
        'Template',         # 0
        'Sonoff Basic',
        'Sonoff RF',
        'Sonoff SV',
        'Sonoff TH',
        'Sonoff Dual',      # 5
        'Sonoff POW',
        'Sonoff 4ch',
        'Sonoff S2X',
        'Slampher',
        'Sonoff Touch',     # 10
        'Sonoff LED',
        '1 Channel',
        '4 Channel',
        'Motor C/AC',
        'ElectroDragon',    # 15
        'EXS Relay(s)',
        'WION',
        'Generic',
        'Sonoff Dev',
        'H801',             # 20
        'Sonoff SC',
        'Sonoff BN-SZ',
        'Sonoff 4ch Pro',
        'Huafan SS',
        'Sonoff Bridge',    # 25
        'Sonoff B1',
        'Ailight',
        'Sonoff T1 1ch',
        'Sonoff T1 2ch',
        'sonoff T1 3ch',    # 30
        'Supla Espablo',
        'Witty Cloud',
        'Yunshan Relay',
        'Magic Home',
        'Luani HVIO',       # 35
        'KMC 70011',
        'Arilux LC01',
        'Arilux LC11',
        'Sonoff dual R2',
        'Arilux LC06',      # 40
        'Sonoff S31',
        'Zengge WF017',
        'Sonoff POW R2',
        'Sonoff iFan02',
        'Blitzwolf SHP',    # 45
        'Shelly 1',
        'Shelly 2',
        'Xiaomi Philips',
        'Neo Coolcam',
        'ESP SwicCh',       # 50
        'Obi Socket',
        'Teckin',
        'APLIC WDP303075',
        'Tuya Dimmer',
        'Gosound SP1 v23',  # 55
        'Armtronix Dimmers',
        'SK03 Outdoor (Tuya)',
        'PS-16-DZ',
        'Teckin US',
        'Manzoku Strip (EU 4)', # 60
        'Obi Socket 2',
        'YTF LR Bridge',
        'Digoo DG-SP202',
        'KA10',
        'Luminea ZX2820',   # 65
        'Mi Desk Lamp',
        'SP10',
        'WAGA CHCZ02MB',
        'SYF05',
        'Sonoff L1',        # 70
        'Sonoff iFan03'     # 71
    ]
    _tasmota_features = [[
        "USE_ENERGY_MARGIN_DETECTION","USE_LIGHT","USE_I2C","USE_SPI",
        "USE_DISCOVERY","USE_ARDUINO_OTA","USE_MQTT_TLS","USE_WEBSERVER",
        "WEBSERVER_ADVERTISE","USE_EMULATION_HUE","MQTT_PUBSUBCLIENT","MQTT_TASMOTAMQTT",
        "MQTT_ESPMQTTARDUINO","MQTT_HOST_DISCOVERY","USE_ARILUX_RF","USE_WS2812",
        "USE_WS2812_DMA","USE_IR_REMOTE","USE_IR_HVAC","USE_IR_RECEIVE",
        "USE_DOMOTICZ","USE_DISPLAY","USE_HOME_ASSISTANT","USE_SERIAL_BRIDGE",
        "USE_TIMERS","USE_SUNRISE","USE_TIMERS_WEB","USE_RULES",
        "USE_KNX","USE_WPS","USE_SMARTCONFIG","USE_ENERGY_POWER_LIMIT"
        ],[
        "USE_CONFIG_OVERRIDE","FIRMWARE_MINIMAL","FIRMWARE_SENSORS","FIRMWARE_CLASSIC",
        "FIRMWARE_KNX_NO_EMULATION","USE_DISPLAY_MODES1TO5","USE_DISPLAY_GRAPH","USE_DISPLAY_LCD",
        "USE_DISPLAY_SSD1306","USE_DISPLAY_MATRIX","USE_DISPLAY_ILI9341","USE_DISPLAY_EPAPER",
        "USE_DISPLAY_SH1106","USE_MP3_PLAYER","USE_PCA9685","USE_TUYA_DIMMER",
        "USE_RC_SWITCH","USE_ARMTRONIX_DIMMERS","USE_SM16716","USE_SCRIPT",
        "USE_EMULATION_WEMO","USE_SONOFF_IFAN","USE_ZIGBEE","NO_EXTRA_4K_HEAP",
        "VTABLES_IN_IRAM","VTABLES_IN_DRAM","VTABLES_IN_FLASH","PIO_FRAMEWORK_ARDUINO_LWIP_HIGHER_BANDWIDTH",
        "PIO_FRAMEWORK_ARDUINO_LWIP2_LOW_MEMORY","PIO_FRAMEWORK_ARDUINO_LWIP2_HIGHER_BANDWIDTH","DEBUG_THEO","USE_DEBUG_DRIVER"
        ],[
        "USE_COUNTER","USE_ADC_VCC","USE_ENERGY_SENSOR","USE_PZEM004T",
        "USE_DS18B20","USE_DS18x20_LEGACY","USE_DS18x20","USE_DHT",
        "USE_SHT","USE_HTU","USE_BMP","USE_BME680",
        "USE_BH1750","USE_VEML6070","USE_ADS1115_I2CDEV","USE_ADS1115",
        "USE_INA219","USE_SHT3X","USE_MHZ19","USE_TSL2561",
        "USE_SENSEAIR","USE_PMS5003","USE_MGS","USE_NOVA_SDS",
        "USE_SGP30","USE_SR04","USE_SDM120","USE_SI1145",
        "USE_SDM630","USE_LM75AD","USE_APDS9960","USE_TM1638"
        ],[
        "USE_MCP230xx","USE_MPR121","USE_CCS811","USE_MPU6050",
        "USE_MCP230xx_OUTPUT","USE_MCP230xx_DISPLAYOUTPUT","USE_HLW8012","USE_CSE7766",
        "USE_MCP39F501","USE_PZEM_AC","USE_DS3231","USE_HX711",
        "USE_PZEM_DC","USE_TX20_WIND_SENSOR","USE_MGC3130","USE_RF_SENSOR",
        "USE_THEO_V2","USE_ALECTO_V2","USE_AZ7798","USE_MAX31855",
        "USE_PN532_I2C","USE_MAX44009","USE_SCD30","USE_HRE",
        "USE_ADE7953","USE_SPS30","USE_VL53L0X","USE_MLX90614",
        "USE_MAX31865","USE_CHIRP","USE_SOLAX_X1","USE_PAJ7620"
        ],[
        "USE_BUZZER","USE_RDM6300","USE_IBEACON","USE_SML_M",
        "USE_INA226","USE_A4988_STEPPER","USE_DDS2382","USE_SM2135",
        "USE_SHUTTER","USE_PCF8574","USE_DDSU666","USE_DEEPSLEEP",
        "USE_SONOFF_SC","USE_SONOFF_RF","USE_SONOFF_L1","USE_EXS_DIMMER",
        "USE_ARDUINO_SLAVE","USE_HIH6","USE_HPMA","USE_TSL2591",
        "","","","",
        "","","","",
        "","","",""
    ]]    
    _mqtt_conn_error = [
        '0: Connection successful',                                # 0
        '1: Connection refused - incorrect protocol version',      # 1
        '2: Connection refused - invalid client identifier',       # 2
        '3: Connection refused - server unavailable',              # 3
        '4: Connection refused - bad username or password',        # 4
        '5: Connection refused - not authorised'                   # 5
    ]
#-------------------------------------------------------------------------------
    def __init__(self, *,
        broker = _DEFAULT_BROKER,
        logconfig_file = _DEFAULT_LOGCONFIG,
        verbose = _DEFAULT_VERBOSE,
        features = _DEFAULT_FEATURES,
        mqtt_timeout = _DEFAULT_MQTT_TIMEOUT,
        http_timeout = _DEFAULT_HTTP_TIMEOUT,
        tasmota = True,
        shellies = False
    ):
        super().__init__()

        global logger
        logger_config(logconfig_file)
        logger = logging.getLogger(__name__)

        self._broker = broker
        self._broker_config = {
            'keep_alive': 10,
            'ping_delay': 1,
            'auto_reconnect': True,
            'reconnect_max_interval': 2,
            'reconnect_retries': 5,
            'check_hostname': False,
            'verify_mode': ssl.CERT_NONE
        }
        self._tasmota = tasmotaDict()
        self._shellies = shelliesDict()
        self._verbose = verbose
        self._features = features
        self._mqtt_timeout = mqtt_timeout
        self._http_timeout = http_timeout
        self._collect_tasmota = tasmota
        self._collect_shellies = shellies
        
#-------------------------------------------------------------------------------
    # async def _get_tasmota(self, *, broker):
    #     if broker:
    #         logger.info(f'sonoff/tasmota discovery')
    #         await self._get_mqtt(
    #             broker = broker,
    #             sub = _SONOFF_SUB,
    #             pub = _SONOFF_PUB
    #         )
    #         logger.info(f'sonoff/tasmota count:{len(self._tasmota.items())}')
    #     else:
    #         logger.error(f'broker not connected')

#-------------------------------------------------------------------------------
    # async def _get_shellies(self, *, broker):
    #     if broker:
    #         logger.info(f'shellies discovery')
    #         await self._get_mqtt(
    #             broker = broker,
    #             sub = _SHELLIES_SUB,
    #             pub = _SHELLIES_PUB
    #         )
    #         logger.info(f'shellies count:{len(self._shellies.items())}')

    #         if len(self._shellies.items()) > 0:
    #             logger.info(f'shellies info retrieval')
    #             await self._get_shellies_info()            
    #     else:
    #         logger.error(f'broker not connected')

#-------------------------------------------------------------------------------
    async def main_func(self):
        logger.info(f'-------------------------------------------------------------------------------')

        l_loop = asyncio.get_running_loop()
        l_broker = await self._connect(broker=self._broker)
        if l_broker:
            l_sub = _ALL_SUB
            l_pub = _ALL_PUB
            if self._collect_tasmota and not self._collect_shellies:
                l_sub = _TASMOTA_SUB
                l_pub = _TASMOTA_PUB
            if not self._collect_tasmota and self._collect_shellies:
                l_sub = _SHELLIES_SUB
                l_pub = _SHELLIES_PUB

            await self._subscribe(broker=l_broker, topics=l_sub)
            await self._publish(broker=l_broker, publish=l_pub)
            await asyncio.wait((
                l_loop.create_task(self._get_mqtt(broker=l_broker, timeout=self._mqtt_timeout)),),
                return_when=asyncio.ALL_COMPLETED)
            await self._unsubscribe(broker=l_broker, topics=_ALL_SUB)
            await self._disconnect(broker=l_broker)
            if self._collect_tasmota:
                logger.info(f'sonoff/tasmota count:{len(self._tasmota.items())}')
            if self._collect_shellies:
                logger.info(f'shellies count:{len(self._shellies.items())}')
                if len(self._shellies.items()) > 0:
                    logger.info(f'shellies info retrieval')
                    await self._get_shellies_info(shellies=self._shellies, timeout=self._http_timeout)            
                    logger.info(f'shellies info retrieved')
        await self._print(verbose=self._verbose, features=self._features)
        print('')

#-------------------------------------------------------------------------------
    async def _connect(self, *,
        broker = 'mqtt://localhost:1883'
    ):
        try:
            l_client_id = f'{_PROGRAM_NAME}-{str(uuid.uuid4())}'
            logger.debug(f'Connecting mqtt broker:{broker} client_id:{l_client_id}')
            l_broker = MQTTClient(client_id=l_client_id, config=self._broker_config)
            l_status = await l_broker.connect(broker)
            l_rc_txt = main_class._mqtt_conn_error[l_status] if l_status < len(main_class._mqtt_conn_error) else f'{l_status}'
            logger.info(f'MQTT connected status: {l_rc_txt}')
            return l_broker
        except ConnectException:
            logger.exception(f'ConnectException broker:{broker} client_id:{l_client_id}')

        return None

#-------------------------------------------------------------------------------
    async def _disconnect(self, *, broker):
        if broker:
            await broker.disconnect()
            logger.info(f'MQTT disconnected')

#-------------------------------------------------------------------------------
    async def _publish(self, *, broker, publish):
        if broker:
            for (l_topic, l_payload) in publish:
                logger.debug(f'publish:{l_topic} payload:{l_payload}')
                await broker.publish(l_topic, l_payload, qos=_DEFAULT_QOS, retain=False)

#-------------------------------------------------------------------------------
    async def _subscribe(self, *, broker, topics):
        if broker:
            l_sub = []
            for l_topic in topics:
                l_sub.append((l_topic, _DEFAULT_QOS))
            logger.debug(f'subscribe:{l_sub}')
            await broker.subscribe(l_sub)

#-------------------------------------------------------------------------------
    async def _unsubscribe(self, *, broker, topics):
        if broker:
            logger.debug(f'unsubscribe:{topics}')
            await broker.unsubscribe(topics)

#-------------------------------------------------------------------------------
    async def _get_mqtt(self, *,
        broker,
        timeout
    ):
        if not broker:
            logger.error(f'Broker None')
            return False

        l_run = True
        try:
            while l_run:
                message = await broker.deliver_message(timeout=timeout)
                packet = message.publish_packet
                l_data = str(packet.payload.data.decode())
                # print(l_data)
                try:
                    l_jsondata = json.loads(l_data)
                    # logger.info(f'{packet.variable_header.topic_name} => {l_jsondata}')
                    await self._handle_json(
                        topic = packet.variable_header.topic_name,
                        jsondata = json.loads(l_data))
                except:
                    pass
        except ClientException as ce:
            logger.error(f'ClientException: {ce}')
            return False
        except asyncio.TimeoutError:
            # logger.error(f'TimeoutError')
            pass
        
        return True

#-------------------------------------------------------------------------------
    async def _handle_json(self, *, 
        topic,
        jsondata
    ):

        if 'sonoff' in topic or 'tasmota' in topic:
            try:
                if 'sonoff' in topic:
                    l_iidx = topic.index('sonoff') + len('sonoff') + 1
                else :
                    l_iidx = topic.index('tasmota') + len('tasmota') + 1
                logger.debug(f'topic:{topic} data:{jsondata}')
                # l_id = topic[l_iidx:l_iidx+6]
                l_sidx = topic.rindex('/')
                l_id = topic[:l_sidx]
                l_sta = topic[l_sidx+1:]
                # logger.debug(f'iidx:{l_iidx} sidx:{l_sidx} id:{l_id} sta:{l_sta}')
            except:
                logger.exception()
            l_tasmota = self._tasmota.get(l_id)
            if not l_tasmota:
                l_tasmota = self._tasmota.add(l_id, tasmotaItem())
            try:
                if 'STATUS' == l_sta:
                    l_s = jsondata['Status']
                    l_tasmota.module = l_s['Module']
                    l_tasmota.topic = l_s['Topic']
                    l_tasmota.friendlyname = l_s['FriendlyName']
                elif 'STATUS5' == l_sta:
                    l_s = jsondata['StatusNET']
                    l_tasmota.hostname = l_s['Hostname']
                    l_tasmota.ipaddress = l_s['IPAddress']
                    l_tasmota.mac = l_s['Mac']
                elif 'STATUS6' == l_sta:
                    l_s = jsondata['StatusMQT']
                    l_tasmota.mqtthost = l_s['MqttHost']
                    l_tasmota.mqttport = l_s['MqttPort']
                    l_tasmota.mqttuser = l_s['MqttUser']
                    l_tasmota.mqttclient = l_s['MqttClient']
                    l_tasmota.fbtopic = 'cmnd/' + l_s['MqttClient'] + '_fb'
                elif 'STATUS2' == l_sta:
                    l_s = jsondata['StatusFWR']
                    l_tasmota.version = l_s['Version']
                    l_tasmota.builddate = l_s['BuildDateTime']
                    l_tasmota.core = l_s['Core']
                elif 'STATUS1' == l_sta:
                    l_s = jsondata['StatusPRM']
                    l_tasmota.grouptopic = l_s['GroupTopic']
                    l_tasmota.otaurl = l_s['OtaUrl']
                    l_tasmota.restartreason = l_s['RestartReason']
                    l_tasmota.uptime = l_s['Uptime']
                    l_tasmota.startuputc = l_s['StartupUTC']
                elif 'STATUS11' == l_sta:
                    l_s = jsondata['StatusSTS']
                    l_w = l_s['Wifi']
                    l_tasmota.wifi_ssid = l_w['SSId']
                    l_tasmota.wifi_bssid = l_w['BSSId']
                    l_tasmota.wifi_ch = l_w['Channel']
                    l_tasmota.wifi_rssi = l_w['RSSI']
                elif 'STATUS4' == l_sta:
                    l_s = jsondata['StatusMEM']
                    l_tasmota.features = l_s['Features']
                elif 'RESULT' == l_sta:
                    try:
                        l_tasmota.fulltopic = jsondata['FullTopic']
                    except:
                        pass
            except:
                logger.exception(f'topic:{topic} json: {jsondata}')
        elif 'shellies/announce' in topic:
            logger.debug(f'topic:{topic} data:{jsondata}')
            l_id = jsondata['id']
            l_shellies = self._shellies.get(l_id)
            if not l_shellies:
                l_shellies = self._shellies.add(l_id, shelliesItem())
            try:
                l_mac = jsondata['mac']
                l_shellies.mac = l_mac[:2] + ':' + l_mac[2:4] + ':' + l_mac[4:6] + ':' + l_mac[6:8] + ':' + l_mac[8:10] + ':' + l_mac[10:12]
                l_shellies.ipaddress = jsondata['ip']
                l_shellies.fw = jsondata['fw_ver']
                l_shellies.new_fw = bool(jsondata['new_fw'])
                l_shellies.shelly_type = l_id[:l_id.rfind('-')]
            except:
                logger.exception(f'topic:{topic} json: {jsondata}')
            # logger.debug(f'shellies:{self._shellies}')
        elif 'shellies/http' in topic:
            logger.debug(f'topic:{topic} data:{jsondata}')
            l_id = topic[topic.rfind('/')+1:]
            l_shellies = self._shellies.get(l_id)
            if not l_shellies:
                logger.error(f'id:{l_id} does not exist')
                return
            try:
                l_shellies.device_type = jsondata['device']['type']
                l_shellies.hostname = jsondata['device']['hostname']
                l_shellies.mqtt = bool(jsondata['mqtt']['enable'])
                l_shellies.mqtthost = jsondata['mqtt']['server']
                l_shellies.mqttuser = jsondata['mqtt']['user']
                l_shellies.wifi_ssid = jsondata['wifi_sta']['ssid']
                l_shellies.sntp_server = jsondata['sntp']['server']
                l_shellies.tz = jsondata['timezone']
                l_shellies.tz_autodetect = jsondata['tzautodetect']

            except:
                logger.exception(f'id:{l_id} json: {jsondata}')

#-------------------------------------------------------------------------------
    async def _get_shellies_info(self, *, shellies, timeout):
        l_session = None
        l_loop = asyncio.get_running_loop()
        l_tasks = []
        if len(shellies.items()):
            try:
                l_session = await self._aiohttp_session(timeout=timeout)
                if l_session:
                    for l_key, l_item in shellies.items():
                        l_tasks.append(l_loop.create_task(self._get_http(session=l_session, url=f'http://{l_item.ipaddress}/settings', key=l_key)))
                if l_tasks:
                    await asyncio.wait(l_tasks, return_when=asyncio.ALL_COMPLETED)
            except:
                logger.exception(f'')
                pass
            finally:
                if l_session:
                    await l_session.close()
        else:
            logger.info(f'No shellies found')

#-------------------------------------------------------------------------------
    async def _aiohttp_session(self, *, timeout):
        try:
            l_connector = aiohttp.TCPConnector(
                limit=10, 
                limit_per_host=0
            )
            l_session = aiohttp.ClientSession(
                timeout = aiohttp.ClientTimeout(connect=timeout, total=(timeout)),
                connector = l_connector
            )
            # logger.info(f'aiohttp session created')
            return l_session
        except:
            logger.exception('*** exception')
            return None

#-------------------------------------------------------------------------------
    async def _get_http(self, *, session, url, key ) -> str:
        logger.debug(f'key:{key} url:{url}')

        try:
            async with session.get(url) as l_resp:
                if l_resp.status == 200:
                    l_data = await l_resp.text()
                    if l_data:
                        await self._handle_json(topic=f'shellies/http/{key}', jsondata=json.loads(l_data))
                        # logger.debug(f'{key}: {l_data}')
        except asyncio.CancelledError:
            logger.warning(f'CancelledError: {url}')
        except asyncio.TimeoutError:
            logger.error(f'TimeoutError: {url}')
        except ClientConnectorCertificateError:
            logger.critical(f'ClientConnectorCertificateError. set ssl_verify: false or get authentic ssl certificate: {url}')
        except ClientConnectorError:
            logger.error(f'ClientConnectorError: {url}')
        except ServerTimeoutError:
            logger.error(f'ServerTimeoutError: {url}')
        except:
            logger.error(f'failed url:{url}')
            logger.exception(f'*** exception')

#-------------------------------------------------------------------------------
    async def _print(self, *,
        verbose = _DEFAULT_VERBOSE,
        features = _DEFAULT_FEATURES
    ):
        if len(self._tasmota.items()) > 0:
            l_sorted = self._tasmota.sort()
            if verbose == 'basic':
                print('')
                print(f'SONOFF / TASMOTA: {len(self._tasmota.items())}')
                print(f'HOSTNAME                  IP ADDRESS         MAC ADDRESS        FRIENDLY NAME')
                print(f'------------------------------------------------------------------------------------')

            for l_key, l_item in l_sorted.items():
                if verbose == 'basic':
                    l_friendlyname = ''
                    for l_idx, l_name in enumerate(l_item.friendlyname):
                        if l_idx:
                            l_friendlyname += ', '
                        l_friendlyname += l_name
                    print(f'{l_item.hostname:25s} {l_item.ipaddress:18s} {l_item.mac:18s} {l_friendlyname}')
                else:
                    print(f'')
                    if l_item.module < len(main_class._tasmota_module_type):
                        print(f'MODULE TYPE:        {main_class._tasmota_module_type[l_item.module]} ({l_item.module})')
                    else:
                        print(f'MODULE TYPE:        {l_item.module}')
                    l_friendlyname = ''
                    for l_idx, l_name in enumerate(l_item.friendlyname):
                        if l_idx:
                            l_friendlyname += ', '
                        l_friendlyname += l_name
                    print(f'FRIENDLY NAME:      {l_friendlyname}')
                    print(f'HOSTNAME:           {l_item.hostname}')
                    print(f'IP ADDRESS:         {l_item.ipaddress}')
                    print(f'MAC ADDRESS:        {l_item.mac}')
                    print(f'MQTT BROKER:        {l_item.mqtthost}:{l_item.mqttport}')
                    print(f'MQTT USER:          {l_item.mqttuser}')
                    print(f'MQTT CLIENT ID:     {l_item.mqttclient}')
                    print(f'MQTT FULL TOPIC:    {l_item.fulltopic}')
                    print(f'MQTT GROUP TOPIC:   {l_item.grouptopic}')
                    print(f'MQTT TOPIC:         {l_item.topic}')
                    print(f'MQTT FB TOPIC:      {l_item.fbtopic}')
                    print(f'WIFI SSID:          {l_item.wifi_ssid}')
                    print(f'WIFI BSSID:         {l_item.wifi_bssid}')
                    print(f'WIFI CHANNEL:       {l_item.wifi_ch}')
                    print(f'WIFI RSSI:          {l_item.wifi_rssi}')
                    print(f'STARTUP UTC:        {l_item.startuputc}')
                    print(f'UPTIME:             {l_item.uptime}')
                    print(f'RESTART REASON:     {l_item.restartreason}')
                    print(f'FW VERSION:         {l_item.version}')
                    print(f'FW BUILD DATE:      {l_item.builddate}')
                    print(f'FW CORE VERSION:    {l_item.core}')
                    print(f'OTA URL:            {l_item.otaurl}')
                    print(f'FEATURES:           {l_item.features}')
                    if features:
                        await self._print_tasmota_features(features=l_item.features)

        if len(self._shellies.items()) > 0:
            if verbose == 'basic':
                print('')
                print(f'SHELLIES: {len(self._shellies.items())}')
                print(f'SHELLY TYPE               IP ADDRESS         MAC ADDRESS    ')
                print(f'---------------------------------------------------------------')
            for l_key, l_item in self._shellies.items():
                if verbose == 'basic':
                    print(f'{l_item.hostname:25s} {l_item.ipaddress:18s} {l_item.mac:18s}')
                else:
                    print(f'')
                    print(f'DEVICE TYPE:        {l_item.device_type}')
                    print(f'SHELLY TYPE:        {l_item.shelly_type}')
                    print(f'HOSTNAME:           {l_item.hostname}')
                    print(f'IP ADDRESS:         {l_item.ipaddress}')
                    print(f'MAC ADDRESS:        {l_item.mac}')
                    print(f'MQTT BROKER:        {l_item.mqtthost}')
                    print(f'MQTT USER:          {l_item.mqttuser}')
                    print(f'WIFI SSID:          {l_item.wifi_ssid}')
                    print(f'SNTP SERVER:        {l_item.sntp_server}')
                    print(f'TIMEZONE:           {l_item.tz}')
                    print(f'TZ AUTO DETECT:     {l_item.tz_autodetect}')
                    print(f'FIRMWARE:           {l_item.fw}')
                    print(f'NEW FW AVAILABLE:   {str(l_item.new_fw)}')
                # print(f'{l_key}: {l_item}')

#-------------------------------------------------------------------------------
    async def _print_tasmota_features(self, *, features):
        l_features = []
        for l_idx, feature in enumerate(features):
            i_feature = int(feature,16)
            if l_idx == 0:
                l_features.append(str("LCID = {}".format(i_feature & 0xFFFF)))
            else:
                for i in range(len(main_class._tasmota_features[l_idx -1])):
                    if (i_feature >> i) & 1:
                        l_features.append(main_class._tasmota_features[l_idx -1][i])

        l_features.sort()
        for l_idx, fea in enumerate(l_features):
            print("{0:30s}  ".format(fea), end='')
            if not (l_idx % 4):
                print('')
        print('')

# ==============================================================================
if __name__ == '__main__':
# ==============================================================================
    l_parser = argparse.ArgumentParser(prog=_PROGRAM_PY, description=_PROGRAM_NAME)
    l_parser.add_argument('-b', '--broker', help='<broker> ........ MQTT broker (mqtt://<user>:<password>@<host>:<port>)', default=_DEFAULT_BROKER, required=True, type=str, dest='broker', metavar='<broker>')
    l_parser.add_argument('-v', '--verbose', help='<verbose> ....... verbose level', choices=['basic', 'full'], default=_DEFAULT_VERBOSE, required=False, type=str, dest='verbose', metavar='<verbose>')
    l_parser.add_argument('-f', '--features', help='<features> ..... decode tasmota features', action='store_true', required=False, dest='features')
    l_parser.add_argument('-t', '--mqtttimeout', help='<mqtttimeout> .. MQTT timeout', default=_DEFAULT_MQTT_TIMEOUT, required=False, type=int, dest='mqtttimeout', metavar='<mqtttimeout>')
    l_parser.add_argument('-s', '--httptimeout', help='<httptimeout> .. HTTP timeout', default=_DEFAULT_HTTP_TIMEOUT, required=False, type=int, dest='httptimeout', metavar='<httptimeout>')
    l_parser.add_argument('--tasmota',  help='<tasmota> ....... collect tasmota', action='store_true', required=False, dest='tasmota')
    l_parser.add_argument('--shellies', help='<shellies> ...... connect shellies', action='store_true', required=False, dest='shellies')
    l_args = l_parser.parse_args()

    print('')
    print ('--- {0:s} STARTED {1:s} ---'.format(_PROGRAM_NAME.upper(), str(_dt.now())))
    print('')
    print('version:             {0}'.format(_VERSION))
    print('python:              {0}'.format(platform.python_version()))
    print('cpu count:           {0}'.format(cpu_count()))
    print('parent pid:          {0}'.format((os.getpid())))

    print('')
    print('COMMANDLINE ARGUMENTS')
    print('-'*21)
    print('broker:              {0}'.format(l_args.broker))
    print('mqtt timeout:        {0}'.format(l_args.mqtttimeout))
    print('http timeout:        {0}'.format(l_args.httptimeout))
    print('verbose level:       {0}'.format(l_args.verbose))
    print('decode features:     {0}'.format(l_args.features))
    if not l_args.tasmota and not l_args.shellies:
        l_args.tasmota = True
        l_args.shellies = True
    print('tasmota:             {0}'.format(l_args.tasmota))
    print('shellies:            {0}'.format(l_args.shellies))
    print('')

    l_main = main_class(
        broker = l_args.broker,
        verbose = l_args.verbose,
        features = l_args.features,
        mqtt_timeout = l_args.mqtttimeout,
        http_timeout = l_args.httptimeout,
        tasmota = l_args.tasmota,
        shellies = l_args.shellies

    )
    try:
        asyncio.get_event_loop().run_until_complete(l_main.main_func())
    except (Exception) as l_e:
        logger.exception('***')
