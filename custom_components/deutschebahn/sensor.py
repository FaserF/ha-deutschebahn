from datetime import timedelta, datetime
import logging
from typing import Optional
import async_timeout
from deutsche_bahn_api.api_authentication import ApiAuthentication
from deutsche_bahn_api.station_helper import StationHelper
from deutsche_bahn_api.timetable_helper import TimetableHelper
#import deutsche_bahn_api

from homeassistant import config_entries, core
from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.typing import ConfigType

from .const import (
    ATTRIBUTION,
    CONF_DESTINATION,
    CONF_START,
    CONF_OFFSET,
    CONF_ONLY_DIRECT,
    CONF_MAX_CONNECTIONS,
    CONF_UPDATE_INTERVAL,
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: core.HomeAssistant, entry: ConfigType, async_add_entities: AddEntitiesCallback
):
    """Setup sensors from a config entry created in the integrations UI."""
    config = hass.data[DOMAIN][entry.entry_id]
    scan_interval = timedelta(minutes=config.get(CONF_UPDATE_INTERVAL, 2))
    _LOGGER.debug(f"Sensor async_setup_entry Using scan interval: {scan_interval}")

    if entry.options:
        config.update(entry.options)

    sensors = DeutscheBahnSensor(config, hass, scan_interval)
    async_add_entities([sensors], update_before_add=True)


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
        self.only_direct = config[CONF_ONLY_DIRECT]
        self.scan_interval = scan_interval

        # Initialize API authentication
        self.api_auth = ApiAuthentication(
            config[CONF_CLIENT_ID],
            config[CONF_CLIENT_SECRET],
        )
        if not self.api_auth.test_credentials():
            raise ValueError("Invalid Deutsche Bahn API credentials.")

        # Station helpers
        self.station_helper = StationHelper()
        self.timetable_helper = None

        # Connections
        self.connections = []

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
        attributes = {
            "departures": self.connections,
            "last_update": datetime.now(),
        }
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
                _LOGGER.debug(f"Updating data for {self.start} -> {self.goal}")

                # Find stations
                start_station = self.station_helper.find_stations_by_name(self.start)[0]
                goal_station = self.station_helper.find_stations_by_name(self.goal)[0]

                # Initialize timetable helper
                self.timetable_helper = TimetableHelper(start_station, self.api_auth)

                # Get timetable
                raw_connections = self.timetable_helper.get_timetable()
                self.connections = self.timetable_helper.get_timetable_changes(raw_connections)

                if not self.connections:
                    self.connections = []
                    self._available = True

                if self.connections:
                    first_connection = self.connections[0]
                    departure_time = first_connection.get("departure")
                    delay = first_connection.get("delay", 0)
                    self._state = f"{departure_time} (+{delay})" if delay else departure_time

        except Exception as e:
            self._available = False
            _LOGGER.exception(f"Error updating Deutsche Bahn data: {e}")
