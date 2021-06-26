import logging
import requests
import json
import voluptuous as vol
from datetime import timedelta
import homeassistant.helpers.config_validation as cv

from homeassistant.components.climate import (ClimateEntity, PLATFORM_SCHEMA)

from homeassistant.components.climate.const import (
	HVAC_MODE_DRY, HVAC_MODE_FAN_ONLY, HVAC_MODE_AUTO, HVAC_MODE_HEAT, HVAC_MODE_COOL, HVAC_MODE_OFF,
	SWING_OFF, SWING_HORIZONTAL,
	SUPPORT_FAN_MODE, SUPPORT_TARGET_TEMPERATURE, SUPPORT_SWING_MODE,
	FAN_AUTO, FAN_HIGH, FAN_MEDIUM, FAN_LOW,
)

from homeassistant.const import (
	ATTR_TEMPERATURE,
	CONF_NAME, CONF_HOST, CONF_SCAN_INTERVAL,
	TEMP_CELSIUS
)

SCAN_INTERVAL = timedelta(seconds=1)

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = 'Innova Climate'
SUPPORT_FLAGS = SUPPORT_TARGET_TEMPERATURE | SUPPORT_FAN_MODE | SUPPORT_SWING_MODE
HVAC_MODES = [HVAC_MODE_OFF, HVAC_MODE_DRY, HVAC_MODE_FAN_ONLY, HVAC_MODE_AUTO, HVAC_MODE_HEAT, HVAC_MODE_COOL]
FAN_MODES = [FAN_AUTO, FAN_LOW, FAN_MEDIUM, FAN_HIGH]
SWING_MODES = [SWING_OFF, SWING_HORIZONTAL]

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
	vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
	vol.Required(CONF_HOST): cv.string,
	vol.Optional(CONF_SCAN_INTERVAL, default=SCAN_INTERVAL):
		vol.All(cv.time_period, cv.positive_timedelta),
})


def setup_platform(hass, config, add_entities, discovery_info=None):
	# async def setup_platform_async(hass, config, async_add_devices, discovery_info=None):
	_LOGGER.info('Setting up Innova climate platform')

	name = config.get(CONF_NAME)
	ip_addr = config.get(CONF_HOST)

	_LOGGER.info('Adding Innova climate device to hass')
	add_entities([
		InnovaClimate(hass, name, ip_addr)
	], True)


class InnovaClimate(ClimateEntity):
	def __init__(self, hass, name, ip_addr):
		_LOGGER.info('Initialize the Innova climate device')
		self.hass = hass
		self._name = name
		self._ip_addr = ip_addr

		self._target_temperature = None
		self._current_temperature = None

		self._hvac_mode = None
		self._fan_mode = None
		self._swing_mode = None

		self._available = False

		self._serial = None
		self._device_name = None

		self.innova_update_status()

	def innova_update_status(self):
		try:
			response = requests.get("http://" + self._ip_addr + "/api/v/1/status")
			response_json = response.json()

			self._target_temperature = response_json["RESULT"]["sp"]
			self._current_temperature = response_json["RESULT"]["t"]

			self._fan_mode = FAN_AUTO
			self._fan_mode = FAN_LOW if response_json["RESULT"]["fs"] == 1 else self._fan_mode
			self._fan_mode = FAN_MEDIUM if response_json["RESULT"]["fs"] == 2 else self._fan_mode
			self._fan_mode = FAN_HIGH if response_json["RESULT"]["fs"] == 3 else self._fan_mode

			self._swing_mode = SWING_OFF if response_json["RESULT"]["fr"] == 7 else SWING_HORIZONTAL

			if response_json["RESULT"]["ps"] == 1:
				self._hvac_mode = HVAC_MODE_OFF
				self._hvac_mode = HVAC_MODE_HEAT if response_json["RESULT"]["wm"] == 0 else self._hvac_mode
				self._hvac_mode = HVAC_MODE_COOL if response_json["RESULT"]["wm"] == 1 else self._hvac_mode
				self._hvac_mode = HVAC_MODE_DRY if response_json["RESULT"]["wm"] == 3 else self._hvac_mode
				self._hvac_mode = HVAC_MODE_FAN_ONLY if response_json["RESULT"]["wm"] == 4 else self._hvac_mode
				self._hvac_mode = HVAC_MODE_AUTO if response_json["RESULT"]["wm"] == 5 else self._hvac_mode
			else:
				self._hvac_mode = HVAC_MODE_OFF

			self._device_name = response_json["setup"]["name"]

			if self._name == DEFAULT_NAME:
				self._name += "("+self._device_name+")"

			_LOGGER.info('TargetTemp:'+str(self._target_temperature) + ' CurrentTemp:'+str(self._current_temperature) + ' Fan:' + self._fan_mode + ' Swing:' + self._swing_mode + ' HVAC:' + self._hvac_mode)

			self._available = True
		except requests.exceptions.ConnectTimeout:
			self._available = False
		except requests.exceptions.ConnectionError:
			self._available = False
		except Exception as e:
			_LOGGER.error("Error while updating", e)

	@property
	def available(self):
		return self._available

	def update(self):
		_LOGGER.info('update()')
		self.innova_update_status()
		self.schedule_update_ha_state()


	@property
	def name(self):
		return self._name

	@property
	def temperature_unit(self):
		return TEMP_CELSIUS

	@property
	def current_temperature(self):
		return self._current_temperature

	@property
	def min_temp(self):
		return 15

	@property
	def max_temp(self):
		return 30

	@property
	def target_temperature_low(self):
		return 15

	@property
	def target_temperature_high(self):
		return 30

	@property
	def target_temperature(self):
		return self._target_temperature

	@property
	def target_temperature_step(self):
		return 1

	@property
	def hvac_mode(self):
		return self._hvac_mode

	@property
	def swing_mode(self):
		return self._swing_mode


	@property
	def fan_mode(self):
		return self._fan_mode

	@property
	def swing_modes(self):
		return SWING_MODES

	@property
	def hvac_modes(self):
		return HVAC_MODES

	@property
	def fan_modes(self):
		return FAN_MODES

	@property
	def supported_features(self):
		return SUPPORT_FLAGS

	def set_temperature(self, **kwargs):
		_LOGGER.info('set_temperature(): ' + str(kwargs.get(ATTR_TEMPERATURE)))
		try:
			requests.post("http://" + self._ip_addr + "/api/v/1/set/setpoint", data={
				"p_temp": kwargs.get(ATTR_TEMPERATURE),
			})

			self._available = True
		except requests.exceptions.ConnectTimeout:
			self._available = False
		except requests.exceptions.ConnectionError:
			self._available = False
		except json.decoder.JSONDecodeError:
			_LOGGER.error('set_fan_mode(): Failed to decode JSON data')
			pass
		except Exception as e:
			_LOGGER.error("Error while setting temperature", e)
		self.innova_update_status()
		self.schedule_update_ha_state()

	def set_swing_mode(self, swing_mode):
		_LOGGER.info('Set swing mode(): ' + str(swing_mode))
		try:
			requests.post("http://" + self._ip_addr + "/api/v/1/set/feature/rotation", data={
				"value": 7 if swing_mode == SWING_OFF else 0,
			})

			self._available = True
		except requests.exceptions.ConnectTimeout:
			self._available = False
		except requests.exceptions.ConnectionError:
			self._available = False
		except json.decoder.JSONDecodeError:
			_LOGGER.error('set_fan_mode(): Failed to decode JSON data')
			pass
		except Exception as e:
			_LOGGER.error("Error while setting swing mode", e)
		self.innova_update_status()
		self.schedule_update_ha_state()

	def set_fan_mode(self, fan):
		_LOGGER.info('set_fan_mode(): ' + str(fan))
		try:
			requests.post("http://" + self._ip_addr + "/api/v/1/set/fan", data={
				"value": FAN_MODES.index(fan),
			})

			self._available = True
		except requests.exceptions.ConnectTimeout:
			self._available = False
		except requests.exceptions.ConnectionError:
			self._available = False
		except json.decoder.JSONDecodeError:
			_LOGGER.error('set_fan_mode(): Failed to decode JSON data')
			pass
		except Exception as e:
			_LOGGER.error("Error while setting fan mode", e)
		self.innova_update_status()
		self.schedule_update_ha_state()

	def set_hvac_mode(self, hvac_mode):
		_LOGGER.info('set_hvac_mode(): ' + str(hvac_mode))
		try:
			self.innova_update_status()
			if hvac_mode == HVAC_MODE_OFF:
				if self._hvac_mode != HVAC_MODE_OFF:
					requests.post("http://" + self._ip_addr + "/api/v/1/power/off", data={})
			else:
				if self._hvac_mode == HVAC_MODE_OFF:
					requests.post("http://" + self._ip_addr + "/api/v/1/power/on", data={})

				if hvac_mode == HVAC_MODE_AUTO:
					requests.post("http://" + self._ip_addr + "/api/v/1/set/mode/auto", data={})
				if hvac_mode == HVAC_MODE_HEAT:
					requests.post("http://" + self._ip_addr + "/api/v/1/set/mode/heating", data={})
				if hvac_mode == HVAC_MODE_COOL:
					requests.post("http://" + self._ip_addr + "/api/v/1/set/mode/cooling", data={})
				if hvac_mode == HVAC_MODE_DRY:
					requests.post("http://" + self._ip_addr + "/api/v/1/set/mode/dehumidification", data={})
				if hvac_mode == HVAC_MODE_FAN_ONLY:
					requests.post("http://" + self._ip_addr + "/api/v/1/set/mode/fanonly", data={})

			self._available = True
		except requests.exceptions.ConnectTimeout:
			self._available = False
		except requests.exceptions.ConnectionError:
			self._available = False
		except json.decoder.JSONDecodeError:
			_LOGGER.error('set_fan_mode(): Failed to decode JSON data')
			pass
		except Exception as e:
			_LOGGER.error("Error while setting hvac mode", e)
		self.innova_update_status()
		self.schedule_update_ha_state()
