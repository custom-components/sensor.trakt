"""Home Assistant component to feed the Upcoming Media Lovelace card with Trakt user's upcoming TV episodes.

https://github.com/custom-components/sensor.trakt
https://github.com/custom-cards/upcoming-media-card
"""

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_CLIENT_ID, CONF_CLIENT_SECRET
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_oauth2_flow

from .config_flow import TraktOAuth2FlowHandler
from .coordinator import TraktDataUpdateCoordinator
from .oauth_impl import TraktOauth2Implementation

PLATFORMS = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Trakt from config entry."""
    TraktOAuth2FlowHandler.async_register_implementation(
        hass,
        TraktOauth2Implementation(
            hass, entry.data[CONF_CLIENT_ID], entry.data[CONF_CLIENT_SECRET]
        ),
    )

    implementation = (
        await config_entry_oauth2_flow.async_get_config_entry_implementation(
            hass, entry
        )
    )

    session = config_entry_oauth2_flow.OAuth2Session(hass, entry, implementation)
    await session.async_ensure_token_valid()

    coordinator = TraktDataUpdateCoordinator(hass, session.token[CONF_ACCESS_TOKEN])
    coordinator.initialize()
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Trakt integration."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options."""
    coordinator: TraktDataUpdateCoordinator = entry.runtime_data
    await coordinator.async_request_refresh()
