"""Bahn.de Custom Component."""
import asyncio
import logging
from datetime import timedelta

from homeassistant import config_entries, core

from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(minutes=2)

async def async_setup_entry(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry
) -> bool:
    """Set up platform from a ConfigEntry."""
    hass.data.setdefault(DOMAIN, {})
    hass_data = dict(entry.data)
    # Registers update listener to update config entry when options are updated.
    unsub_options_update_listener = entry.add_update_listener(options_update_listener)
    # Store a reference to the unsubscribe function to cleanup if an entry is unloaded.
    hass_data["unsub_options_update_listener"] = unsub_options_update_listener
    hass.data[DOMAIN][entry.entry_id] = hass_data

    # Forward the setup to the sensor platform.
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )

    config = hass.data[DOMAIN][entry.entry_id]
    async def async_update_data():
        """Fetch data from Schiene."""
        update_interval=timedelta(minutes=config[CONF_SCAN_INTERVAL])
        async with async_timeout.timeout(update_interval - 1):
            await hass.async_add_executor_job(lambda: data.update())

            if not data.state:
                raise UpdateFailed(f"Error fetching {entry.entry_id} Schiene state")

            return data.state

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"{entry.entry_id} Schiene state",
        update_method=async_update_data,
    )

    return True

async def options_update_listener(
    hass: core.HomeAssistant, config_entry: config_entries.ConfigEntry
):
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)

async def async_update(self):
    """Async wrapper for update method."""
    return await self._hass.async_add_executor_job(self._update)

async def async_unload_entry(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry
) -> bool:
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[hass.config_entries.async_forward_entry_unload(entry, "sensor")]
        )
    )
    # Remove options_update_listener.
    hass.data[DOMAIN][entry.entry_id]["unsub_options_update_listener"]()

    # Remove config entry from domain.
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok