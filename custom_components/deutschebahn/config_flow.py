import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_DESTINATION,
    CONF_START,
    CONF_OFFSET,
    CONF_ONLY_DIRECT,
    CONF_MAX_CONNECTIONS,
    CONF_IGNORED_PRODUCTS,
    CONF_IGNORED_PRODUCTS_OPTIONS,
    CONF_UPDATE_INTERVAL,
)

DOMAIN = "deutschebahn"

_LOGGER = logging.getLogger(__name__)

class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        def __get_option(key: str, default: Any) -> Any:
            return self.config_entry.options.get(
                key, self.config_entry.data.get(key, default)
            )

        if user_input is not None:
            return self.async_create_entry(data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_OFFSET, default=0): cv.positive_int,
                    vol.Required(CONF_MAX_CONNECTIONS, default=2): vol.All(vol.Coerce(int), vol.Range(min=1, max=6)),
                    vol.Required(CONF_IGNORED_PRODUCTS, default=[]): cv.multi_select(CONF_IGNORED_PRODUCTS_OPTIONS),
                    vol.Required(CONF_ONLY_DIRECT, default=False): cv.boolean,
                    vol.Optional(CONF_UPDATE_INTERVAL, 2): cv.positive_int,
                }
            ),
        )

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow"""

    VERSION = 2
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_START] + " to " + user_input[CONF_DESTINATION])
            self._abort_if_unique_id_configured()
            _LOGGER.debug("Initialized new deutschebahn with id: {unique_id}")
            return self.async_create_entry(title=user_input[CONF_START] + " - " + user_input[CONF_DESTINATION], data=user_input)

        data_schema = vol.Schema(
            {
                vol.Required(CONF_START): cv.string,
                vol.Required(CONF_DESTINATION): cv.string,
                vol.Required(CONF_OFFSET, default=0): cv.positive_int,
                vol.Required(CONF_MAX_CONNECTIONS, default=2): vol.All(vol.Coerce(int), vol.Range(min=1, max=6)),
                vol.Required(CONF_IGNORED_PRODUCTS, default=[]): cv.multi_select(CONF_IGNORED_PRODUCTS_OPTIONS),
                vol.Required(CONF_ONLY_DIRECT, default=False): cv.boolean,
                vol.Optional(CONF_UPDATE_INTERVAL, 2): cv.positive_int,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)
