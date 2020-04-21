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
import voluptuous as vol
from homeassistant.const import (
    CONF_ACCESS_TOKEN,
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_EXCLUDE,
    CONF_SCAN_INTERVAL,
)
from homeassistant.helpers import aiohttp_client, config_entry_oauth2_flow
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_time_interval
from trakt.calendar import MyShowCalendar
from trakt.tv import TVShow

from . import config_flow
from .const import (
    CARD_DEFAULT,
    CONF_DAYS,
    DATA_TRAKT_CRED,
    DATA_UPDATED,
    DEFAULT_DAYS,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    OAUTH2_AUTHORIZE,
    OAUTH2_TOKEN,
)

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_CLIENT_ID): cv.string,
                vol.Required(CONF_CLIENT_SECRET): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass, config) -> bool:
    """Set up Trakt integration."""
    hass.data[DOMAIN] = {}

    if DOMAIN not in config:
        return True

    config_flow.TraktOAuth2FlowHandler.async_register_implementation(
        hass,
        config_entry_oauth2_flow.LocalOAuth2Implementation(
            hass,
            DOMAIN,
            config[DOMAIN][CONF_CLIENT_ID],
            config[DOMAIN][CONF_CLIENT_SECRET],
            OAUTH2_AUTHORIZE,
            OAUTH2_TOKEN,
        ),
    )
    hass.data.setdefault(
        DATA_TRAKT_CRED,
        {
            CONF_CLIENT_ID: config[DOMAIN][CONF_CLIENT_ID],
            CONF_CLIENT_SECRET: config[DOMAIN][CONF_CLIENT_SECRET],
        },
    )

    return True


async def async_setup_entry(hass, entry) -> bool:
    """Set up Trakt from config entry."""

    implementation = await config_entry_oauth2_flow.async_get_config_entry_implementation(
        hass, entry
    )

    session = config_entry_oauth2_flow.OAuth2Session(hass, entry, implementation)
    await session.async_ensure_token_valid()
    trakt_data = Trakt_Data(hass, entry, session)

    if not await trakt_data.async_setup():
        return False
    hass.data[DOMAIN] = trakt_data

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )
    return True


async def async_unload_entry(hass, entry):
    """Unload Trakt integration."""
    if hass.data[DOMAIN].unsub_timer:
        hass.data[DOMAIN].unsub_timer()

    await hass.config_entries.async_forward_entry_unload(entry, "sensor")

    hass.data.pop(DOMAIN)

    return True


class Trakt_Data:
    """Represent Trakt data."""

    def __init__(self, hass, config_entry, implementation):
        """Initialize trakt data."""
        self.hass = hass
        self.config_entry = config_entry
        self.session = config_entry_oauth2_flow.OAuth2Session(
            hass, config_entry, implementation
        )
        self.unsub_timer = None
        self.details = {}
        self.calendar = None

    @property
    def days(self):
        """Return number of days to look forward for movies/shows."""
        return self.config_entry.options[CONF_DAYS]

    @property
    def exclude(self):
        """Return list of show titles to exclude."""
        return self.config_entry.options[CONF_EXCLUDE] or []

    async def async_update(self, *_):
        """Update Trakt data."""
        card_json = [CARD_DEFAULT]

        try:
            self.calendar = await self.hass.async_add_executor_job(
                MyShowCalendar, {CONF_DAYS: self.days}
            )
        except trakt.errors.OAuthException:
            _LOGGER.error(
                "Trakt api is unauthrized. Please remove the entry and reconfigure."
            )
            return

        if not self.calendar:
            _LOGGER.warning("Trakt upcoming calendar is empty")
            return

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

        self.details = json.dumps(card_json)
        _LOGGER.debug("Trakt data updated")

        async_dispatcher_send(self.hass, DATA_UPDATED)

    async def async_setup(self):
        """Set up Trakt Data."""
        await self.async_add_options()
        trakt.core.OAUTH_TOKEN = self.session.token[CONF_ACCESS_TOKEN]
        trakt.core.CLIENT_ID = self.hass.data[DATA_TRAKT_CRED][CONF_CLIENT_ID]
        trakt.core.CLIENT_SECRET = self.hass.data[DATA_TRAKT_CRED][CONF_CLIENT_SECRET]

        try:
            await self.async_update()
        except trakt.errors.OAuthException:
            _LOGGER.error(
                "Trakt api is unauthrized. Please remove the entry and reconfigure."
            )
            return False

        await self.async_set_scan_interval(
            self.config_entry.options[CONF_SCAN_INTERVAL]
        )
        self.config_entry.add_update_listener(self.async_options_updated)

        return True

    async def async_add_options(self):
        """Add options for entry."""
        if not self.config_entry.options:

            options = {
                CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
                CONF_DAYS: DEFAULT_DAYS,
                CONF_EXCLUDE: None,
            }

            self.hass.config_entries.async_update_entry(
                self.config_entry, options=options
            )

    async def async_set_scan_interval(self, scan_interval):
        """Update scan interval."""

        if self.unsub_timer is not None:
            self.unsub_timer()
        self.unsub_timer = async_track_time_interval(
            self.hass, self.async_update, timedelta(minutes=scan_interval)
        )

    @staticmethod
    async def async_options_updated(hass, entry):
        """Triggered by config entry options updates."""
        await hass.data[DOMAIN].async_set_scan_interval(
            entry.options[CONF_SCAN_INTERVAL]
        )
        await hass.data[DOMAIN].async_update()


def days_until(date):
    """Calculate days until."""
    show_date = dt_util.as_local(date)
    now = dt_util.as_local(dt_util.now())
    return int((show_date - now).total_seconds() / 86400)
