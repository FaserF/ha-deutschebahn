"""deutschebahn sensor platform."""
from datetime import timedelta, datetime
import logging
from typing import Any, Callable, Dict, Optional, Set
import re

import schiene
import async_timeout

from homeassistant import config_entries, core
from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.const import ATTR_ATTRIBUTION
from homeassistant.helpers.entity_platform import AddEntitiesCallback
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.typing import (
    ConfigType,
    HomeAssistantType,
    DiscoveryInfoType,
)
import homeassistant.util.dt as dt_util
import voluptuous as vol

from .const import (
    ATTRIBUTION,
    CONF_DESTINATION,
    CONF_START,
    CONF_OFFSET,
    CONF_ONLY_DIRECT,
    CONF_MAX_CONNECTIONS,
    CONF_IGNORED_PRODUCTS,
    ATTR_DATA,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(minutes=2)

async def async_setup_entry(
    hass: HomeAssistantType, entry: ConfigType, async_add_entities
):
    """Setup sensors from a config entry created in the integrations UI."""
    config = hass.data[DOMAIN][entry.entry_id]
    _LOGGER.debug("Sensor async_setup_entry")
    if entry.options:
        config.update(entry.options)
    sensors = DeutscheBahnSensor(config, hass)
    async_add_entities(
        [
            DeutscheBahnSensor(config, hass)
        ],
        update_before_add=True
    )

class DeutscheBahnSensor(SensorEntity):
    """Implementation of a Deutsche Bahn sensor."""

    def __init__(self, config, hass: HomeAssistantType):
        super().__init__()
        self._name = f"{config[CONF_START]} to {config[CONF_DESTINATION]}"
        self._state = None
        self._available = True
        self.hass = hass
        self.updated = datetime.now()
        self.start = config[CONF_START]
        self.goal = config[CONF_DESTINATION]
        self.offset = timedelta(minutes=config[CONF_OFFSET])
        self.max_connections: int = config.get(CONF_MAX_CONNECTIONS, 2)
        self.ignored_products = config.get(CONF_IGNORED_PRODUCTS, [])
        self.only_direct = config[CONF_ONLY_DIRECT]
        self.schiene = schiene.Schiene()
        self.connections = [{}]

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self._name
        #return f"{self.start}_{self.goal}"

    @property
    def icon(self):
        """Return the icon for the frontend."""
        return "mdi:train"

    @property
    def state(self) -> Optional[str]:
        if self._state is not None:
            return self._state
        else:
            return "Unknown"

    @property
    def native_value(self):
        """Return the departure time of the next train."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        if len(self.connections) > 0:
            connections = self.connections[0].copy()
            for cons in range(1,len(self.connections)):
                if len(self.connections) > cons:
                    connections[f"next_{cons}"] = self.connections[cons]["departure"]
                    connections[f"next_{cons}_delay"] = self.connections[cons]["delay"]
                    connections[f"next_{cons}_canceled"] = self.connections[cons]["canceled"]
                    connections[f"next_{cons}_arrival"] = self.connections[cons]["arrival"]
        else:
            connections = None
        connections["departures"] = self.connections
        return connections

    async def async_update(self):
        try:
            with async_timeout.timeout(30):
                hass = self.hass
                """Pull data from the bahn.de web page."""
                _LOGGER.debug(f"Update the connection data for '{self.start}' '{self.goal}'")
                self.connections = await hass.async_add_executor_job(
                        fetch_schiene_connections, hass, self
                    )

                if not self.connections:
                    self.connections = [{}]
                    self._available = True
                connections_count = len(self.connections)

                if connections_count > 0:
                    for con in self.connections:
                        # Detail info is not useful. Having a more consistent interface
                        # simplifies usage of template sensors.
                        if "details" in con:
                            #_LOGGER.debug(f"Processing connection: {con}")
                            con.pop("details")
                            delay = con.get("delay", {"delay_departure": 0, "delay_arrival": 0})
                            con["delay"] = delay["delay_departure"]
                            con["delay_arrival"] = delay["delay_arrival"]
                            con["ontime"] = con.get("ontime", False)
                            #self.attrs[ATTR_DATA] = self.connections
                            #self.attrs[ATTR_ATTRIBUTION] = f"last updated {datetime.now()} \n{ATTRIBUTION}"

                    if self.connections[0].get("delay", 0) != 0:
                        self._state = f"{self.connections[0]['departure']} + {self.connections[0]['delay']}"
                    else:
                        self._state = self.connections[0].get("departure", "Unknown")
                else:
                    _LOGGER.exception(f"Data from DB for direction: '{self.start}' '{self.goal}' was empty, retrying at next sync run. Maybe also check if you have spelled your start and destination correct?")
                    self._available = False

        except:
            self._available = False
            _LOGGER.exception(f"Cannot retrieve data for direction: '{self.start}' '{self.goal}' - Most likely it is a temporary API issue from DB and will stop working after a HA restart/some time.")

def fetch_schiene_connections(hass, self):
    raw_data = self.schiene.connections(
        self.start,
        self.goal,
        dt_util.as_local(dt_util.utcnow() + self.offset),
        self.only_direct,
    )
    _LOGGER.debug(f"Fetched data: {raw_data}")

    data = []
    for connection in raw_data:
        if len(data) == self.max_connections:
            break
        elif set(connection["products"]).intersection(self.ignored_products):
            continue

        data.append(connection)
    _LOGGER.debug(f"Filtered data: {data}")

    return data
