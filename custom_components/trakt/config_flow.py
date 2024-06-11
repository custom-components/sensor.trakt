"""Config flow for Trakt."""

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import (
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_EXCLUDE,
    CONF_NAME,
)
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.helpers.config_entry_oauth2_flow import AbstractOAuth2FlowHandler

from .const import CONF_DAYS, DEFAULT_DAYS, DEFAULT_NAME, DOMAIN
from .coordinator import TraktDataUpdateCoordinator
from .oauth_impl import TraktOauth2Implementation


class TraktOAuth2FlowHandler(AbstractOAuth2FlowHandler, domain=DOMAIN):
    """Handle a Trakt config flow."""

    DOMAIN = DOMAIN

    def __init__(self) -> None:
        """Initialize the Trakt config flow."""
        super().__init__()
        self.config = None

    @property
    def logger(self) -> logging.Logger:
        """Return logger."""
        return logging.getLogger(__name__)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle a flow started by a user."""
        if user_input:
            await self.async_set_unique_id(user_input[CONF_CLIENT_ID])
            self._abort_if_unique_id_configured()

            self.config = user_input

            self.async_register_implementation(
                self.hass,
                TraktOauth2Implementation(
                    self.hass,
                    user_input[CONF_CLIENT_ID],
                    user_input[CONF_CLIENT_SECRET],
                ),
            )

            return await super().async_step_user()

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

    async def async_oauth_create_entry(
        self, data: dict[str, Any]
    ) -> config_entries.ConfigFlowResult:
        """Create an entry for the flow."""
        self.config.update(data)
        return self.async_create_entry(title=self.config[CONF_NAME], data=self.config)

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return TraktOptionsFlowHandler(config_entry)


class TraktOptionsFlowHandler(config_entries.OptionsFlowWithConfigEntry):
    """Handle Trakt options."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> None:
        """Manage the Trakt options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        coordinator: TraktDataUpdateCoordinator = self.config_entry.runtime_data
        options = {
            vol.Optional(
                CONF_DAYS,
                default=self.config_entry.options.get(CONF_DAYS, DEFAULT_DAYS),
            ): vol.All(
                selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1, step=1, mode=selector.NumberSelectorMode.BOX
                    ),
                ),
                vol.Coerce(int),
            )
        }
        if tv_shows := {tv_show.show for tv_show in coordinator.tv_shows}:
            options.update(
                {
                    vol.Optional(
                        CONF_EXCLUDE,
                        default=self.config_entry.options.get(CONF_EXCLUDE),
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=list(tv_shows), multiple=True
                        )
                    )
                }
            )

        return self.async_show_form(step_id="init", data_schema=vol.Schema(options))
