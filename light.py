import logging
import voluptuous as vol
import requests

import homeassistant.helpers.config_validation as cv

from homeassistant.components.light import (
    PLATFORM_SCHEMA, 
    SUPPORT_COLOR,
    SUPPORT_BRIGHTNESS,
    ATTR_BRIGHTNESS, 
    ATTR_RGB_COLOR, 
    Light)

from homeassistant.const import CONF_HOST

import homeassistant.util.color as color_util

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
})

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Solarpath light platform."""
    host = config[CONF_HOST]
    
    lights = json.loads(requests.get(host))
    
    add_entities(SolarpathFixture(light, host) for light in lights)

class SolarpathFixture(Light):
    def __init__(self, light, host):
        self._light = light
        self._host = host
        self._device_eui = light["device_eui"]

    @property
    def name(self):
        return self._light["device_eui"]

    @property
    def is_on(self):
        return self._light["light_on"]

    @property
    def brightness(self) -> int:
        return None

    @property
    def rgb_color(self):
        return None

    async def async_turn_on(self, **kwargs):
        self._light["light_on"] = 1
        requests.post(self._host, json.dumps(self._light))

    async def async_turn_off(self, **kwargs):
        self._light["light_on"] = 0
        requests.post(self._host, json.dumps(self._light))

    def update(self):
        lights = json.loads(requests.get(self._host))
        for light in lights:
            if (light["device_eui"] == self._device_eui):
                self._light = light
                break

