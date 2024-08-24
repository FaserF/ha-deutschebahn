"""deutschebahn sensor platform."""
from datetime import timedelta, datetime
import logging
from typing import Optional
import async_timeout
from urllib.parse import quote

import schiene
import homeassistant.util.dt as dt_util
import requests
from bs4 import BeautifulSoup

from homeassistant import config_entries, core
from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.const import ATTR_ATTRIBUTION
from homeassistant.helpers.entity_platform import AddEntitiesCallback
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import (
    ATTRIBUTION,
    CONF_DESTINATION,
    CONF_START,
    CONF_OFFSET,
    CONF_ONLY_DIRECT,
    CONF_MAX_CONNECTIONS,
    CONF_IGNORED_PRODUCTS,
    CONF_UPDATE_INTERVAL,
    ATTR_DATA,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: core.HomeAssistant, entry: ConfigType, async_add_entities
):
    """Setup sensors from a config entry created in the integrations UI."""
    config = hass.data[DOMAIN][entry.entry_id]
    scan_interval = timedelta(minutes=config.get(CONF_UPDATE_INTERVAL, 2))
    _LOGGER.debug("Sensor async_setup_entry")
    if entry.options:
        config.update(entry.options)
    sensors = DeutscheBahnSensor(config, hass, scan_interval)
    async_add_entities(
        [
            DeutscheBahnSensor(config, hass, scan_interval)
        ],
        update_before_add=True
    )

class DeutscheBahnSensor(SensorEntity):
    """Implementation of a Deutsche Bahn sensor."""

    def __init__(self, config, hass: core.HomeAssistant, scan_interval: timedelta):
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
        self.scan_interval = scan_interval

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self._name

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
        attributes = {}
        if self.connections:
            for con in self.connections:
                if "departure" in con and "arrival" in con:
                    # Parse departure and arrival times
                    departure_time = dt_util.parse_time(con.get("departure"))
                    arrival_time = dt_util.parse_time(con.get("arrival"))
                    if departure_time and arrival_time:
                        # Create datetime objects for departure and arrival times
                        departure_datetime = datetime.combine(datetime.now().date(), departure_time)
                        arrival_datetime = datetime.combine(datetime.now().date(), arrival_time)
                        # Apply delays
                        corrected_departure_time = departure_datetime + timedelta(minutes=con.get("delay", 0))
                        corrected_arrival_time = arrival_datetime + timedelta(minutes=con.get("delay_arrival", 0))
                        # Format and add current departure and arrival times
                        con["departure_current"] = corrected_departure_time.strftime("%H:%M")
                        con["arrival_current"] = corrected_arrival_time.strftime("%H:%M")
        attributes["departures"] = self.connections
        attributes["last_update"] = datetime.now()
        return attributes

    async def async_added_to_hass(self):
        """Call when entity is added to hass."""
        await super().async_added_to_hass()
        self.async_on_remove(
            async_track_time_interval(
                self.hass, self._async_refresh_data, self.scan_interval
            )
        )

    async def _async_refresh_data(self, now=None):
        """Refresh the data."""
        await self.async_update_ha_state(force_refresh=True)

    async def async_update(self):
        try:
            with async_timeout.timeout(30):
                hass = self.hass
                """Pull data from the bahn.de web page."""
                _LOGGER.debug(f"Update the connection data for '{self.start}' '{self.goal}'")
                self.connections = await hass.async_add_executor_job(
                        fetch_schiene_connections, hass, self, self.ignored_products
                    )

                if not self.connections:
                    self.connections = [{}]
                    self._available = True
                connections_count = len(self.connections)

                if connections_count > 0:
                    if connections_count < self.max_connections:
                        _LOGGER.warning(
                            f"Requested {self.max_connections} connections, but only {connections_count} are available."
                        )

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

def fetch_schiene_connections(hass, self, ignored_products):
    """Fetch connections from Schiene API and apply offset filter."""
    try:
        raw_data = self.schiene.connections(
            self.start,
            self.goal,
            dt_util.as_local(dt_util.utcnow() + self.offset),
            self.only_direct,
        )
        _LOGGER.debug(f"Fetched raw data: {raw_data}")

        current_time = dt_util.as_local(dt_util.utcnow() + self.offset)
        _LOGGER.debug(f"Current time with offset: {current_time}")

        data = []
        for connection in raw_data:
            departure_time = dt_util.parse_time(connection.get("departure"))
            if departure_time:
                # Combine date with time, then make sure datetime is aware
                departure_datetime = datetime.combine(datetime.now().date(), departure_time)
                # Assume timezone is the same as current_time's timezone
                departure_datetime = dt_util.as_local(departure_datetime)

                delay_info = connection.get("delay", {"delay_departure": 0, "delay_arrival": 0})
                delay_departure = delay_info.get("delay_departure", 0)
                delay_arrival = delay_info.get("delay_arrival", 0)
                departure_datetime += timedelta(minutes=delay_departure)
                _LOGGER.debug(f"Departure datetime for connection: {departure_datetime}")

                if departure_datetime < current_time:
                    _LOGGER.debug(f"Connection filtered out, departure time {departure_datetime} is before current time {current_time}")
                    continue

            if len(data) == self.max_connections:
                _LOGGER.debug("Reached maximum number of connections to return")
                break
            elif set(connection["products"]).intersection(ignored_products):
                _LOGGER.debug(f"Connection filtered out due to ignored products: {connection['products']}")
                continue

            data.append(connection)

        _LOGGER.debug(f"Filtered data: {data}")
        return data
    except Exception as e:
        _LOGGER.exception(f"Error fetching or processing connections: {e}")
        return []
