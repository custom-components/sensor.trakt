"""
Support for Trakt sensors.

For more details about this platform, please refer to the documentation at
https://github.com/custom-components/sensor.trakt
"""

# WATCHLIST
# UPCOMING CALENDAR
# UP NEXT CALENDAR (SAME?)
# CHECK-IN SERVICE
# SEARCH
# ADD TO WATCHLIST SERVICE

import logging
import voluptuous as vol
import requests
import json
from datetime import timedelta
from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import (PLATFORM_SCHEMA)

__version__ = '0.0.1'

REQUIREMENTS = ['trakt==2.8.2', 'requests_oauthlib==1.0.0']

CONF_CLIENT_ID = 'id'
CONF_CLIENT_SECRET = 'secret'
CONF_USERNAME = 'username'
CONF_DAYS = 'days'

SESSION_PATH = '.trakt'

DATA_UPCOMING = 'trakt_upcoming'

BASE_URL = 'https://api-v2launch.trakt.tv/'
REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'

SCAN_INTERVAL = timedelta(minutes=30)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_CLIENT_ID): cv.string,
    vol.Required(CONF_CLIENT_SECRET): cv.string,
    vol.Required(CONF_USERNAME): cv.string,
    vol.Optional(CONF_DAYS, default=30): cv.positive_int,
})

_CONFIGURING = {}
_LOGGER = logging.getLogger(__name__)

def request_app_setup(hass, config, trakt, add_devices, discovery_info=None):
    """Request configuration steps from the user."""
    from requests.compat import urljoin
    from requests_oauthlib import OAuth2Session
    configurator = hass.components.configurator
    authorization_base_url = urljoin(BASE_URL, '/oauth/authorize')
    oauth = OAuth2Session(config[CONF_CLIENT_ID], redirect_uri=REDIRECT_URI, state=None)
    _LOGGER.error('request_app_setup')

    def trakt_configuration_callback(data):
        """Run when the configuration callback is called."""
        _LOGGER.error('trakt_configuration_callback')
        token_url = urljoin(BASE_URL, '/oauth/token')
        oauth.fetch_token(token_url, client_secret=config[CONF_CLIENT_SECRET], code=data.get('pin_code'))
        trakt.core.OAUTH_TOKEN = oauth.token['access_token']
        _LOGGER.error(oauth.token['access_token'])
        continue_setup_platform(hass, config, trakt, add_devices, discovery_info)

    if 'trakt' not in _CONFIGURING:
        _LOGGER.error('get oauth url')
        authorization_url, _ = oauth.authorization_url(authorization_base_url, username=config[CONF_USERNAME])

    _CONFIGURING['trakt'] = configurator.request_config(
        'Trakt',
        trakt_configuration_callback,
        description="Enter pin code from Trakt: " + authorization_url,
        submit_caption='Verify',
        fields=[{
            'id': 'pin_code',
            'name': "Pin code",
            'type': 'string'}]
    )

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the Trakt component."""
    import trakt
    trakt.core.CLIENT_ID = config[CONF_CLIENT_ID]
    trakt.core.CLIENT_SECRET = config[CONF_CLIENT_SECRET]
    _LOGGER.error('setup_platform')
    # TODO Check if session file already exists and verify that token is still valid
    request_app_setup(hass, config, trakt, add_devices, discovery_info)

def continue_setup_platform(hass, config, trakt, add_devices, discovery_info=None):
    """Set up the Trakt component."""
    if "trakt" in _CONFIGURING:
        _LOGGER.error('continue_setup_platform')
        hass.components.configurator.request_done(_CONFIGURING.pop("trakt"))
        add_devices([TraktMyShowCalendarSensor(hass, config, trakt)], True)

class TraktMyShowCalendarSensor(Entity):
    """Representation of a Trakt My Show Calendar sensor."""

    def __init__(self, hass, config, trakt):
        """Initialize the sensor."""
        self._hass = hass
        self._trakt = trakt
        self._days = config[CONF_DAYS]
        self._state = None
        self._hass.data[DATA_UPCOMING] = {}
        self.update()

    def update(self):
        """Get the latest state of the sensor."""
        import trakt
        from trakt.calendar import MyShowCalendar
        calendar = MyShowCalendar(days=self._days)

        if not calendar:
            return False

        for show in calendar:
            self.hass.data[DATA_UPCOMING][show['title']] = {
                "title": show['title'],
                "description": show.get_description(),
                "season": show['season'],
                "episode": show['episode'],
                "first_aired_date": show['first_aired_date'],
            }

    @property
    def name(self):
        """Return the name of the sensor."""
        return 'Trakt My Upcoming Calendar'

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        return 'mdi:calendar'

    @property
    def device_state_attributes(self):
        """Return the state attributes of the sensor."""
        return self._hass.data[DATA_UPCOMING]
