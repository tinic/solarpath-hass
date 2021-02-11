import logging
import voluptuous as vol
import requests
import json

import homeassistant.helpers.config_validation as cv

from homeassistant.components.light import (
    PLATFORM_SCHEMA, 
    SUPPORT_COLOR,
    SUPPORT_BRIGHTNESS,
    ATTR_BRIGHTNESS, 
    ATTR_HS_COLOR, 
    LightEntity)

from homeassistant.const import CONF_HOST

import homeassistant.util.color as color_util

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
})

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Solarpath light platform."""
    host = config[CONF_HOST]
    request = requests.get(host)
    lights = json.loads(request.text)
    props = { "serial" : 1 }
    add_entities(SolarpathFixture(light, host, props) for light in lights)

class SolarpathFixture(LightEntity):
    def __init__(self, light, host, props):
        self._light = light
        self._host = host
        self._device_eui = light["device_eui"]
        self._unique_id = light["device_eui"]
        self._serial = props["serial"]
        self._hsv = list(color_util.color_RGB_to_hsv(
            light["color"][0] * 255,
            light["color"][1] * 255,
            light["color"][2] * 255))
        props["serial"] += 1

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def name(self):
        return "Solarpath Light " + str(self._serial)

    @property
    def is_on(self):
        return self._light["light_on"]

    @property
    def supported_features(self):
        return SUPPORT_COLOR | SUPPORT_BRIGHTNESS
        
    @property
    def brightness(self) -> int:
        return round(self._hsv[2] * 2.55)

    @property
    def hs_color(self) -> tuple:
        return self._hsv[0], self._hsv[1]

    def turn_on(self, **kwargs):
        if ATTR_HS_COLOR in kwargs:
            self._hsv[0] = kwargs.get(ATTR_HS_COLOR)[0]
            self._hsv[1] = kwargs.get(ATTR_HS_COLOR)[1]

        if ATTR_BRIGHTNESS in kwargs:
            self._hsv[2] = float(kwargs.get(ATTR_BRIGHTNESS) / 2.55)

        rgb = color_util.color_hsv_to_RGB(
            self._hsv[0], 
            self._hsv[1],
            self._hsv[2])

        self._light["color"][0] = float(rgb[0]) / 255
        self._light["color"][1] = float(rgb[1]) / 255
        self._light["color"][2] = float(rgb[2]) / 255

        self._light["light_on"] = 1
        requests.post(self._host, json.dumps([self._light]))

    def turn_off(self, **kwargs):
        self._light["light_on"] = 0
        requests.post(self._host, json.dumps([self._light]))

    def update(self):
        request = requests.get(self._host)
        lights = json.loads(request.text)
        for light in lights:
            if (light["device_eui"] == self._device_eui):
                self._light = light
                self._hsv = list(color_util.color_RGB_to_hsv(
                    light["color"][0] * 255,
                    light["color"][1] * 255,
                    light["color"][2] * 255))
                break

