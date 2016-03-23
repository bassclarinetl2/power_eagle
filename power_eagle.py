#!/usr/bin/env python3
#power_eagle.py
#Requires https://github.com/bassclarinetl2/Eagle-Http-API (Forked and modified for Py3 from https://github.com/rainforestautomation/Eagle-Http-API)


DOMAIN = "power_eagle"

CONF_MAC = None
CONF_FORMAT = 'JSON'
CONF_NOISY = 'False'

currency_names ={840:'US Dollars',124:'Canadian Dollars',36:'Australian Dollars',978:'Euros',826:'UK Pounds'}

import logging

from homeassistant.const import CONF_ACCESS_TOKEN, CONF_USERNAME, CONF_PASSWORD
from homeassistant.helpers.entity import entity
from homeassistant.util import Throttle
from re import *

REQUIREMENTS = ['https://github.com/bassclarinetl2/Eagle-Http-API/archive/master.zip']
_LOGGER = logging.getLogger(__name__)
SENSOR_TYPES ={
	'gateway_zigbee_mac' : ['Eagle Zigbee Mac',None],
	'gateway_firmware_ver' : ['Eagle Firmware Version',None],
	'gateway_hardware_ver' : ['Eagle Hardware Version',None],
	'gateway_mfg' : ['Eagle Manufacturer',None],
	'gateway_model' : ['Eagle Model',None],
	'gateway_firmware_date_code' : ['Eagle Firmware Date Code',None],
	'smart_meter_zigbee_mac' : ['Smart Meter Zigbee Mac Address',None],
	'gateway_to_smart_meter_connection_status' : ['Smart Meter - Eagle Connection Status',None],
	'smart_meter_zigbee_channel' : ['Smart Meter Zigbee Channel',None],
	'instaenous_demand_timestamp' : ["Current Demand Timestamp",None],
	'total_elect_delivered' : ['Meter Reading','kWh'],
	'price_pulled_from_meter_timestamp': ['Price pulled from Meter Timestamp',None],
	'instaenous_price_per_kwh' : ['Price per kwh',None],
	'instaenous_demand_in_kwh' : ['Current demand','kWh'],
	'utility_billing_tier' : ['Utility\'s Billing Tier',None],
	'total_instaenous_cost' : ['Total Cost',None],
	'currency' : ['Currency','USD']

}

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=120)


def setup_platform(hass,config,add_devices,discovery_info=None):
	"""Setup Eagle sensor"""
	from eagle_http_api import * #import eagle-http-api
#	from currency_names import * #Grab curency dict from external file
	from datetime import *


	gw = eagle_http(CONF_USERNAME,CONF_PASSWORD,CONF_ACCESS_TOKEN) #define username, passwd, and cloud id (access token) for rainforestcloud.com (aka the free Rainforest cloud)
	
	if not gw:
		_LOGGER.error(
			"Connection error"
			"Please check you settings for the Eagle Gateway"
			"It's not off is it?")
		return False
	
	if CONF_FORMAT != 'JSON':
		gw.json = False
	else:
		gw.json = True
		
	if CONF_NOISY != 'False':
		gw.noisy = True
	else:
		gw.noisy = False

#		
	dev = []
	try:
		for variable in config['data_points']:
			if variable not in SENSOR_TYPES:
				_LOGGER.error ('Data point:"%s" does not exist',variable)
			else:
				dev.append(PowerEagleSensor(variable,unit))
	except KeyError:
		pass

		add_devices(dev)



class Mac():
    def __init__(self, mac):
        self.mac = mac
    def __str__(self):
        return "%s:%s:%s:%s:%s:%s" % (
            self.mac[0:2],
            self.mac[2:4],
            self.mac[4:6],
            self.mac[6:8],
            self.mac[8:10],
            self.mac[10:12])

class PowerEagleSensor(Entity):
	"""Implementation of an PowerEagle sensor."""

	def __init___(self,sensor_type,unit):
		"""Initalize the sensor."""
		self.client_name = 'Power'
		self._name = SENSOR_TYPES[sensor_type][0]
		self.type = sensor_type
		self_state = None
		self._unit = SENSOR_TYPES[sensor_type][1]
		self.update()

		@property
		def name(self):
		    """return name of the sensor"""
		   return self._name
		@property 
		def state(self):
			"""return state of sensor"""
			return self._state

		@property
		def unit(self):
			"""return unit of measure"""
			return self._unit


		def update(self):
		if CONF_MAC not None: 
			get_network_info(CONF_MAC)
			list_network(CONF_MAC)
			get_network_status(CONF_MAC)
			get_instantaneous_demand(CONF_MAC)
			get_price(CONF_MAC)
			get_message(CONF_MAC)
#			confirm_message(CONF_MAC)
			get_current_summation(CONF_MAC)
			get_history_data(CONF_MAC)
#			set_schedule(CONF_MAC)
			get_schedule(CONF_MAC)
			get_demand_peaks(CONF_MAC)
#			reboot(CONF_MAC)
		else:
			get_network_info()
			list_network()
			get_network_status()
			get_instantaneous_demand()
			get_price()
			get_message()
#			confirm_message()
			get_current_summation()
			get_history_data()
#			set_schedule()
			get_schedule()
			get_demand_peaks()
#			reboot()

		if self.type == 'gateway_zigbee_mac':
			self._state = Mac(str(int(gw.NetworkInfo.DeviceMacId,16))[2:])
		elif self.type == 'gateway_firmware_ver':
			self._state = gw.NetworkInfo.FWVersion
		elif self.type == 'gateway_hardware_ver':
			self._state = gw.NetworkInfo.HWVersion
		elif self.type == 'gateway_mfg':
			self._state = gw.NetworkInfo.Manufacturer
		elif self.type == 'gateway_model':
			self._state = gw.NetworkInfo.ModelId
		elif self.type == 'gateway_firmware_date_code':
			self._state = gw.NetworkInfo.DateCode
		elif self.type == 'smart_meter_zigbee_mac':
			self._state = Mac(str(int(gw.NetworkStatus.CoordMacId,16))[2:])
		elif self.type == 'gateway_to_smart_meter_connection_status':
			self._state = gw.NetworkStatus.Status
		elif self.type == 'smart_meter_zigbee_channel':
			self._state = gw.NetworkStatus.Channel
		elif self.type == 'instaenous_demand_timestamp': #pulled from meter in zigbee time.  Add difference between Unix epoch and zb epoch
			self._state = datetime.fromtimestamp((int(gw.InsantaneousDemand.TimeStamp,16) + 946684800))
		elif self.type == 'total_elect_delivered': #in kwh
			self._state = (float.fromhex(gw.CurrentSummation.SummationDelivered) * int(gw.CurrentSummation.Multiplier,16) ) / int(gw.CurrentSummation.Divisor,16)
		elif self.type == 'price_pulled_from_meter_timestamp':
			self._state = datetime.fromtimestamp((int(gw.PriceCluster.TimeStamp,16) + 946684800))
		elif self.type == 'instaenous_price_per_kwh':
			self._state = float.fromhex(gw.PriceCluster.Price)/(10 ** (int(gw.PriceCluster.TrailingDigits,16)))
		elif self.type == 'instaenous_demand_in_kwh':
			self._state = (int(gw.InstantaneousDemand.Demand,16) * int(gw.InstantaneousDemand.Multiplier,16))/ int(gw.InstantaneousDemand.Divisor,16)
		elif self.type == 'utility_billing_tier':
			self._state = gw.PriceCluster.Tier
		elif self.type == 'total_instaenous_cost':
			self._unit = currency[currency_names[int(gw.PriceCluster.Currency,16)]
			self._state = (float.fromhex(gw.PriceCluster.Price)/(10 ** (int(gw.PriceCluster.TrailingDigits,16))))*((int(gw.InstantaneousDemand.Demand,16) * int(gw.InstantaneousDemand.Multiplier,16))/ int(gw.InstantaneousDemand.Divisor,16) #Convert hex values from GW and determine kwh ((demand*multiplier)/divisor)))


		


##############################################################			
"""
##Definitions to get the Data
gw.json = True #force JSON return? 
gw.noisy = True #Let eagle blab on the cli



##Split the returned Dict into individual vars


timeStamp_price_nix_utc = int(gw.PriceCluster.TimeStamp,16) + 946684800
timeStamp_price_human_local = datetime.fromtimestamp((int(gw.PriceCluster.TimeStamp,16)) + 946684800)

timeStamp_sum_nix_utc = int(gw.CurrentSummation.TimeStamp,16) + 946684800
timeStamp_sum_human_local = datetime.fromtimestamp(timeStamp_price_nix_utc)



#startTime = gw.PriceCluster.StartTime
duration = gw.PriceCluster.Duration
price = gw.PriceCluster.Price
currency = gw.PriceCluster.Currency
decimals = int(gw.PriceCluster.TrailingDigits,16)
tier = gw.PriceCluster.Tier

summation_ts = gw.CurrentSummation.TimeStamp
summation_deliv = (float.fromhex(gw.CurrentSummation.SummationDelivered) * int(gw.CurrentSummation.Multiplier,16) ) / int(gw.CurrentSummation.Divisor,16)
summation_recv = gw.CurrentSummation.SummationReceived









(float.fromhex(gw.PriceCluster.Price)/(10 ** (int(gw.PriceCluster.TrailingDigits,16))))*((int(gw.InstantaneousDemand.Demand,16) * int(gw.InstantaneousDemand.Multiplier,16))/ int(gw.InstantaneousDemand.Divisor,16) #Convert hex values from GW and determine kwh ((demand*multiplier)/divisor)))










factor = float.fromhex(gw.PriceCluster.Price)/(10 ** (int(gw.PriceCluster.TrailingDigits,16)))


#Now that we has the data, we can rebuild it since we have the technology.

inst_demand_kwh = (int(gw.InstantaneousDemand.Demand,16) * int(gw.InstantaneousDemand.Multiplier,16))/ int(gw.InstantaneousDemand.Divisor,16) #Convert hex values from GW and determine kwh ((demand*multiplier)/divisor))
currency_words = currency_names[int(gw.PriceCluster.Currency,16)]
price_per_kwh = float.fromhex(gw.PriceCluster.Price) / factor
inst_cost_h = inst_demand_kwh * price_per_kwh
inst_cost_h_round = round(inst_cost_h,5)

##Begin Simple Testing Code

print ("Eagle Zigbee Mac Addr: " + devMac + "\r")
print ("Firmware Ver: " + fWVer + "\r")
print ("Hardware Ver: " + hWVer + "\r")
print ("Manufacturer: " + mfg + "\r")
print ("Model: " + modelNum + "\r")
print ("FW Date: " + dateCode + "\r")
print ("----------------")
print ("Meter Zigbee Mac Addr: " + meterMacId + "\r")
print ("Eagle --> Meter Connection Status: " + EagleConnStatus + "\r")
print ("Meter Zigbee Channel: " + meterConnChannel + "\r")
print ("----------------")
print ("Demand Timestamp: " + str(timeStamp_instdem_human_local) + "\r")
print ("----------------")
print ("Total Delivered: " + str(summation_deliv) + "\r")
print ("Total Recieved: " + str(int(gw.CurrentSummation.SummationReceived,16)) + "\r" )


print ("Price Last pulled from Meter): " + str(timeStamp_price_human_local) + "\r")
print ("Price Per kWh: " + str(price_per_kwh) + "\r")
print ("Instant Demand (kWh): " + str(inst_demand_kwh) + "\r")
print ("Usage Tier: " + tier +"\r")
print ("----------------")
print ("Current Cost per Hour in " + currency_words + ": " + str(inst_cost_h_round) + "\r")  


##End Simple Testing Code
"""
