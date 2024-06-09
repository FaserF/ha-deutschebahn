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

    unsub_options_update_listener = entry.add_update_listener(options_update_listener)
    hass_data["unsub_options_update_listener"] = unsub_options_update_listener
    hass.data[DOMAIN][entry.entry_id] = hass_data

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )

    async def async_update_data():
        """Fetch data from Schiene."""
        config = hass.data[DOMAIN][entry.entry_id]
        update_interval = config.get("scan_interval", 2)  # Default scan interval
        async with async_timeout.timeout(update_interval - 1):
            # Assuming data.update() is an async function, no need for async_add_executor_job
            await data.update()

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

async def async_unload_entry(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry
) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    hass.data[DOMAIN][entry.entry_id]["unsub_options_update_listener"]()

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
