"""Local implementation of OAuth2 specific to Ondilo to hard code client id and secret and return a proper name."""

from homeassistant.core import HomeAssistant
from homeassistant.helpers.config_entry_oauth2_flow import LocalOAuth2Implementation

from .const import DOMAIN, OAUTH2_AUTHORIZE, OAUTH2_TOKEN


class TraktOauth2Implementation(LocalOAuth2Implementation):
    """Local implementation of OAuth2 specific to Ondilo to hard code client id and secret and return a proper name."""

    def __init__(self, hass: HomeAssistant, client_id: str, client_secret: str) -> None:
        """Just init default class with default values."""
        super().__init__(
            hass,
            DOMAIN,
            client_id,
            client_secret,
            OAUTH2_AUTHORIZE,
            OAUTH2_TOKEN,
        )

    @property
    def name(self) -> str:
        """Name of the implementation."""
        return "trakt"
