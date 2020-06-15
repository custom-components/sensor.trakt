"""
Home Assistant component to feed the Upcoming Media Lovelace card with
Trakt user's upcoming TV episodes.

https://github.com/custom-components/sensor.trakt

https://github.com/custom-cards/upcoming-media-card
"""
import asyncio
import json
import logging
from datetime import timedelta

import async_timeout
import homeassistant.util.dt as dt_util
import trakt
from homeassistant import config_entries, core
from homeassistant.const import (
    CONF_ACCESS_TOKEN,
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_EXCLUDE,
    CONF_SCAN_INTERVAL,
)
from homeassistant.helpers import aiohttp_client, config_entry_oauth2_flow
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from trakt.calendar import MyShowCalendar
from trakt.tv import TVShow

from . import config_flow
from .const import (
    CARD_DEFAULT,
    CONF_DAYS,
    DEFAULT_DAYS,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    OAUTH2_AUTHORIZE,
    OAUTH2_TOKEN,
)
from homeassistant.exceptions import ConfigEntryNotReady

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass, config) -> bool:
    """Trakt integration doesn't support configuration.yaml."""

    return True


async def async_setup_entry(hass, entry) -> bool:
    """Set up Trakt from config entry."""

    config_flow.TraktOAuth2FlowHandler.async_register_implementation(
        hass,
        config_entry_oauth2_flow.LocalOAuth2Implementation(
            hass,
            DOMAIN,
            entry.data[CONF_CLIENT_ID],
            entry.data[CONF_CLIENT_SECRET],
            OAUTH2_AUTHORIZE,
            OAUTH2_TOKEN,
        ),
    )

    implementation = await config_entry_oauth2_flow.async_get_config_entry_implementation(
        hass, entry
    )

    session = config_entry_oauth2_flow.OAuth2Session(hass, entry, implementation)
    await session.async_ensure_token_valid()

    coordinator = Trakt_Data(hass, entry, session)
    if not await coordinator.async_setup():
        return False

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )

    return True


async def async_unload_entry(hass, entry) -> bool:
    """Unload Trakt integration."""
    if hass.data[DOMAIN][entry.entry_id].unsub_timer:
        hass.data[DOMAIN][entry.entry_id].unsub_timer()

    await hass.config_entries.async_forward_entry_unload(entry, "sensor")

    hass.data[DOMAIN].pop(entry.entry_id)

    return True


class Trakt_Data(DataUpdateCoordinator):
    """Represent Trakt data."""

    def __init__(
        self,
        hass: core.HomeAssistant,
        config_entry: config_entries.ConfigEntry,
        session: config_entry_oauth2_flow.OAuth2Session,
    ):
        """Initialize trakt data."""
        self.hass = hass
        self.config_entry = config_entry
        self.session = session
        self.unsub_timer = None
        self.calendar = {}

        super().__init__(
            self.hass,
            _LOGGER,
            name=DOMAIN,
            update_method=self.async_update,
            update_interval=timedelta(
                minutes=self.config_entry.options.get(
                    CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                )
            ),
        )

    @property
    def days(self):
        """Return number of days to look forward for movies/shows."""
        return self.config_entry.options.get(CONF_DAYS, DEFAULT_DAYS)

    @property
    def exclude(self):
        """Return list of show titles to exclude."""
        return self.config_entry.options.get(CONF_EXCLUDE) or []

    @property
    def scan_interval(self):
        """Return update interval."""
        return self.config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    async def async_update(self, *_):
        """Update Trakt data."""
        card_json = [CARD_DEFAULT]

        try:
            self.calendar = await self.hass.async_add_executor_job(
                MyShowCalendar, None, self.days
            )
        except trakt.errors.TraktInternalException:
            _LOGGER.error("Trakt api encountered an internal error.")
            raise UpdateFailed

        if not self.calendar:
            _LOGGER.warning("Trakt upcoming calendar is empty")

        for show in self.calendar:
            if not show or show.show in self.exclude:
                continue

            try:
                show_details = await self.hass.async_add_executor_job(
                    TVShow.search, show.show, show.year
                )
            except AttributeError:
                _LOGGER.error("Unable to retrieve show details for " + show.show)

            if not show_details:
                continue

            if days_until(show.airs_at) < 0:
                continue
            if days_until(show.airs_at) <= 7:
                release = "$day, $time"
            else:
                release = "$day, $date $time"

            session = aiohttp_client.async_get_clientsession(self.hass)
            try:
                with async_timeout.timeout(10):
                    response = await session.get(
                        f"http://api.tmdb.org/3/tv/{str(show_details[0].tmdb)}?api_key=0eee347e2333d7a97b724106353ca42f",
                    )
            except asyncio.TimeoutError:
                _LOGGER.warning("api.themoviedb.org is not responding")
                continue

            if response.status != 200:
                _LOGGER.warning("Error retrving information from api.themoviedb.org")
                continue

            tmdb_json = await response.json()

            image_url = "https://image.tmdb.org/t/p/w%s%s"

            card_item = {
                "airdate": show.airs_at.isoformat() + "Z",
                "release": release,
                "flag": False,
                "title": show.show,
                "episode": show.title,
                "number": "S" + str(show.season).zfill(2) + "E" + str(show.number),
                "rating": tmdb_json.get("vote_average", ""),
                "poster": image_url % ("500", tmdb_json.get("poster_path", "")),
                "fanart": image_url % ("780", tmdb_json.get("backdrop_path", "")),
                "runtime": tmdb_json.get("episode_run_time")[0]
                if len(tmdb_json.get("episode_run_time", [])) > 0
                else "",
                "studio": tmdb_json.get("networks")[0].get("name", "")
                if len(tmdb_json.get("networks", [])) > 0
                else "",
            }
            card_json.append(card_item)

        return json.dumps(card_json)

    async def async_setup(self):
        """Set up Trakt Data."""
        trakt.core.OAUTH_TOKEN = self.session.token[CONF_ACCESS_TOKEN]
        trakt.core.CLIENT_ID = self.config_entry.data[CONF_CLIENT_ID]

        try:
            await self.async_refresh()
        except trakt.errors.OAuthException:
            _LOGGER.error(
                "Trakt api is unauthrized. Please remove the entry and reconfigure."
            )
            return False

        if not self.last_update_success:
            raise ConfigEntryNotReady
        self.config_entry.add_update_listener(async_options_updated)

        return True


async def async_options_updated(hass, entry):
    """Triggered by config entry options updates."""
    hass.data[DOMAIN][entry.entry_id].update_interval = timedelta(
        minutes=entry.options[CONF_SCAN_INTERVAL]
    )
    await hass.data[DOMAIN][entry.entry_id].async_request_refresh()


def days_until(date):
    """Calculate days until."""
    show_date = dt_util.as_local(date)
    now = dt_util.as_local(dt_util.now())
    return int((show_date - now).total_seconds() / 86400)
