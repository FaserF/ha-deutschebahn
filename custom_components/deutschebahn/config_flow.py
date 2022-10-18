"""Config flow"""
import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv

from .const import (  # pylint: disable=unused-import
    CONF_DESTINATION,
    CONF_START,
    CONF_OFFSET,
    CONF_ONLY_DIRECT,
)
DOMAIN = "deutschebahn"

_LOGGER = logging.getLogger(__name__)


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
            return self.async_create_entry(title=user_input[CONF_START] + " - " + user_input[CONF_DESTINATION], data=user_input)

            _LOGGER.debug(
                "Initialized new deutschebahn with id: {unique_id}"
            )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_START): str,
                vol.Required(CONF_DESTINATION): str,
                vol.Required(CONF_OFFSET, default=0): cv.positive_int,
                vol.Required(CONF_ONLY_DIRECT, default=False): cv.boolean,
            },
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )