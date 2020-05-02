"""Config flow for Trakt."""
import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import (
    CONF_NAME,
    CONF_EXCLUDE,
    CONF_SCAN_INTERVAL,
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
)
from homeassistant.core import callback
from homeassistant.helpers import config_entry_oauth2_flow
from .const import (
    CONF_DAYS,
    DEFAULT_DAYS,
    DEFAULT_NAME,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    OAUTH2_AUTHORIZE,
    OAUTH2_TOKEN,
)


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

    def __init__(self):
        """Initialize the Trakt config flow."""
        super().__init__()
        self.config = None

    async def async_step_user(self, user_input=None):
        """Handle a flow started by a user."""
        if user_input:
            await self.async_set_unique_id(user_input[CONF_CLIENT_ID])
            self._abort_if_unique_id_configured()

            self.config = user_input

            TraktOAuth2FlowHandler.async_register_implementation(
                self.hass,
                config_entry_oauth2_flow.LocalOAuth2Implementation(
                    self.hass,
                    DOMAIN,
                    user_input[CONF_CLIENT_ID],
                    user_input[CONF_CLIENT_SECRET],
                    OAUTH2_AUTHORIZE,
                    OAUTH2_TOKEN,
                ),
            )

            return await self.async_step_pick_implementation()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
                    vol.Required(CONF_CLIENT_ID): str,
                    vol.Required(CONF_CLIENT_SECRET): str,
                }
            ),
        )

    async def async_oauth_create_entry(self, data):
        """Create an entry for the flow."""
        self.config.update(data)
        return self.async_create_entry(title=self.config[CONF_NAME], data=self.config)


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
                CONF_EXCLUDE, default=self.config_entry.options.get(CONF_EXCLUDE, "-"),
            ): str,
        }

        return self.async_show_form(step_id="init", data_schema=vol.Schema(options))
