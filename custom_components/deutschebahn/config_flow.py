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

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_START] + "-" + user_input[CONF_DESTINATION])
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=user_input[CONF_START], data=user_input)

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


def validate_options(user_input, errors):
    """Validate the options in the OptionsFlow.
    This is an extra validation step because the validators
    in `EXTRA_VALIDATION` cannot be serialized to json.
    """
    for key, (validate, _) in EXTRA_VALIDATION.items():
        # these are unserializable validators
        value = user_input.get(key)
        try:
            if value is not None and value != NONE_STR:
                validate(value)
        except vol.Invalid:
            _LOGGER.exception("Configuration option %s=%s is incorrect", key, value)
            errors["base"] = "option_error"


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle a option flow"""

    def __init__(self, config_entry: config_entries.ConfigEntry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Handle options flow."""
        conf = self.config_entry
        if conf.source == config_entries.SOURCE_IMPORT:
            return self.async_show_form(step_id="init", data_schema=None)
        errors = {}
        if user_input is not None:
            validate_options(user_input, errors)
            if not errors:
                return self.async_create_entry(title="", data=user_input)

        options_schema = {}
        for name, default, validation in VALIDATION_TUPLES:
            key = vol.Optional(name, default=conf.options.get(name, default))
            value = to_replace.get(name, validation)
            options_schema[key] = value

        return self.async_show_form(
            step_id="init", data_schema=vol.Schema(options_schema), errors=errors
        )