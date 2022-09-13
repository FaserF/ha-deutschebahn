"""Support for information about the German train system."""
from __future__ import annotations

from datetime import timedelta
import logging

import schiene
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.const import CONF_OFFSET
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant import config_entries, core
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
import homeassistant.util.dt as dt_util

from typing import Any, Callable, Dict, Optional

import async_timeout

from .const import (
    ATTRIBUTION,
    CONF_EMAIL,
    CONF_PASSWORD,
    CONF_LATITUDE_FS,
    CONF_LONGITUDE_FS,
    CONF_DISTANCE,
    ATTR_BASKETS,
    ATTR_ID,
    ATTR_DESCRIPTION,
    ATTR_UNTIL,
    ATTR_PICTURE,
    ATTR_ADDRESS,
    ATTR_MAPS_LINK,

    DOMAIN,
)

ICON = "mdi:train"
SCAN_INTERVAL = timedelta(minutes=2)
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistantType, entry: ConfigType, async_add_entities
):
    """Setup sensors from a config entry created in the integrations UI."""
    config = hass.data[DOMAIN][entry.entry_id]
    _LOGGER.debug("Sensor async_setup_entry")
    if entry.options:
        config.update(entry.options)
    sensors = FoodsharingSensor(config, hass)
    async_add_entities(sensors, update_before_add=True)
    async_add_entities(
        [
            DeutscheBahnSensor(config, hass)
        ],
        update_before_add=True
    )

class DeutscheBahnSensor(SensorEntity):
    """Implementation of a Deutsche Bahn sensor."""

    def __init__(self, config):
        """Initialize the sensor."""
        start = config[CONF_START]
        destination = config[CONF_DESTINATION]
        offset = config[CONF_OFFSET]
        only_direct = config[CONF_ONLY_DIRECT]

        self._name = f"{start} to {goal}"
        self.data = SchieneData(start, goal, offset, only_direct)
        self._state = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def icon(self):
        """Return the icon for the frontend."""
        return ICON

    @property
    def native_value(self):
        """Return the departure time of the next train."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        connections = self.data.connections[0]
        if len(self.data.connections) > 1:
            connections["next"] = self.data.connections[1]["departure"]
        if len(self.data.connections) > 2:
            connections["next_on"] = self.data.connections[2]["departure"]
        return connections

    def update(self) -> None:
        """Get the latest delay from bahn.de and updates the state."""
        self.data.update()
        self._state = self.data.connections[0].get("departure", "Unknown")
        if self.data.connections[0].get("delay", 0) != 0:
            self._state += f" + {self.data.connections[0]['delay']}"


class SchieneData:
    """Pull data from the bahn.de web page."""

    def __init__(self, start, goal, offset, only_direct):
        """Initialize the sensor."""
        self.start = start
        self.goal = goal
        self.offset = offset
        self.only_direct = only_direct
        self.schiene = schiene.Schiene()
        self.connections = [{}]

    def update(self):
        """Update the connection data."""
        self.connections = self.schiene.connections(
            self.start,
            self.goal,
            dt_util.as_local(dt_util.utcnow() + self.offset),
            self.only_direct,
        )

        if not self.connections:
            self.connections = [{}]

        for con in self.connections:
            # Detail info is not useful. Having a more consistent interface
            # simplifies usage of template sensors.
            if "details" in con:
                con.pop("details")
                delay = con.get("delay", {"delay_departure": 0, "delay_arrival": 0})
                con["delay"] = delay["delay_departure"]
                con["delay_arrival"] = delay["delay_arrival"]
                con["ontime"] = con.get("ontime", False)