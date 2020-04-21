"""Config flow for Trakt."""
import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_EXCLUDE, CONF_SCAN_INTERVAL
from homeassistant.core import callback
from homeassistant.helpers import config_entry_oauth2_flow
from .const import CONF_DAYS, DEFAULT_DAYS, DEFAULT_SCAN_INTERVAL, DOMAIN


class TraktOAuth2FlowHandler(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN
):
    """Handle a Trakt config flow."""

    DOMAIN = DOMAIN
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    @property
    def logger(self) -> logging.Logger:
        """Return logger."""
        return logging.getLogger(__name__)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return TraktOptionsFlowHandler(config_entry)


class TraktOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Trakt options."""

    def __init__(self, config_entry):
        """Initialize Trakt options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the Trakt options."""
        if user_input is not None:
            user_input[CONF_EXCLUDE] = user_input[CONF_EXCLUDE].split(",")
            return self.async_create_entry(title="", data=user_input)

        options = {
            vol.Optional(
                CONF_SCAN_INTERVAL,
                default=self.config_entry.options.get(
                    CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                ),
            ): int,
            vol.Optional(
                CONF_DAYS,
                default=self.config_entry.options.get(CONF_DAYS, DEFAULT_DAYS),
            ): int,
            vol.Optional(
                CONF_EXCLUDE, default=self.config_entry.options.get(CONF_EXCLUDE, None),
            ): str,
        }

        return self.async_show_form(step_id="init", data_schema=vol.Schema(options))
