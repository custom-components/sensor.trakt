"""Trakt calendar data coordinator."""

import asyncio
from datetime import timedelta
import json
import logging
from typing import Any

from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET, CONF_EXCLUDE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
import homeassistant.util.dt as dt_util
import trakt
from trakt.calendar import MyShowCalendar  # pylint: disable=no-name-in-module
from trakt.errors import TraktException  # pylint: disable=no-name-in-module
from trakt.tv import TVShow  # pylint: disable=no-name-in-module

from .const import CARD_DEFAULT, CONF_DAYS, DEFAULT_DAYS, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class TraktDataUpdateCoordinator(DataUpdateCoordinator[str]):
    """Represent Trakt data."""

    def __init__(
        self,
        hass: HomeAssistant,
        token: str,
    ) -> None:
        """Initialize trakt data."""
        self.hass = hass
        self.token = token
        self.tv_shows: list[TVShow] = []

        super().__init__(
            self.hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=DEFAULT_SCAN_INTERVAL),
        )

    @property
    def days(self) -> int:
        """Return number of days to look forward for shows."""
        return self.config_entry.options.get(CONF_DAYS, DEFAULT_DAYS)

    @property
    def exclude(self) -> list[str]:
        """Return list of show titles to exclude."""
        return self.config_entry.options.get(CONF_EXCLUDE, [])

    async def _async_update_data(self) -> list[dict[str,Any]]:
        """Update Trakt data."""
        card_json: list[dict[str, Any]] = [CARD_DEFAULT]
        try:
            self.tv_shows = await self.hass.async_add_executor_job(
                MyShowCalendar, None, self.days
            )
        except TraktException as err:
            raise UpdateFailed(
                f"Trakt api encountered an internal error: {err}"
            ) from err
        if self.tv_shows:
            tasks = [
                self.get_show_data(tv_show)
                for tv_show in self.tv_shows
                if tv_show.show not in self.exclude
            ]
            results = await asyncio.gather(*tasks)
            card_json += [card_item for card_item in results if card_item is not None]

        return card_json

    async def get_show_data(self, show: TVShow) -> dict[str, Any] | None:
        """Get TV show data."""

        try:
            show_details = await self.hass.async_add_executor_job(
                TVShow.search, show.show, show.year
            )
        except AttributeError:
            _LOGGER.error("Unable to retrieve show details for %s", show.show)

        if not show_details:
            return None

        if days_until(show.airs_at) < 0:
            return None
        if days_until(show.airs_at) <= 7:
            release = "$day, $time"
        else:
            release = "$day, $date $time"

        session = aiohttp_client.async_get_clientsession(self.hass)
        try:
            async with asyncio.timeout(10):
                response = await session.get(
                    f"http://api.tmdb.org/3/tv/{show_details[0].tmdb}?api_key=0eee347e2333d7a97b724106353ca42f",
                )
        except TimeoutError:
            return None

        if response.status != 200:
            return None

        tmdb_json = await response.json()

        image_url = "https://image.tmdb.org/t/p/w%s%s"

        return {
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

    def initialize(self) -> None:
        """Initialize Trakt data."""
        trakt.core.OAUTH_TOKEN = self.token
        trakt.core.CLIENT_ID = self.config_entry.data[CONF_CLIENT_ID]
        trakt.core.CLIENT_SECRET = self.config_entry.data[CONF_CLIENT_SECRET]


def days_until(date):
    """Calculate days until."""
    show_date = dt_util.as_local(date)
    now = dt_util.as_local(dt_util.now())
    return int((show_date - now).total_seconds() / 86400)
