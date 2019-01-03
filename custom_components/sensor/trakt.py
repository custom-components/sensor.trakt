"""
Support for Trakt sensors.

For more details about this platform, please refer to the documentation at
https://github.com/custom-components/sensor.trakt
"""
import json
import logging
from datetime import timedelta

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.entity import Entity

__version__ = '0.0.3'

REQUIREMENTS = ['trakt==2.8.2', 'requests_oauthlib==1.0.0']

CONF_CLIENT_ID = 'id'
CONF_CLIENT_SECRET = 'secret'
CONF_USERNAME = 'username'
CONF_DAYS = 'days'
CONF_NAME = 'name'

TOKEN_FILE = '.trakt.conf'

DATA_UPCOMING = 'trakt_upcoming'

BASE_URL = 'https://api-v2launch.trakt.tv/'
REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'

SCAN_INTERVAL = timedelta(minutes=30)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_CLIENT_ID): cv.string,
    vol.Required(CONF_CLIENT_SECRET): cv.string,
    vol.Required(CONF_USERNAME): cv.string,
    vol.Optional(CONF_DAYS, default=30): cv.positive_int,
    vol.Optional(CONF_NAME, default='Trakt Upcoming Calendar'): cv.string,
})

_CONFIGURING = {}
_LOGGER = logging.getLogger(__name__)

def request_app_setup(hass, config, add_devices, discovery_info=None):
    """Request configuration steps from the user."""
    from requests.compat import urljoin
    from requests_oauthlib import OAuth2Session
    configurator = hass.components.configurator
    authorization_base_url = urljoin(BASE_URL, '/oauth/authorize')
    oauth = OAuth2Session(config[CONF_CLIENT_ID], redirect_uri=REDIRECT_URI, state=None)

    def trakt_configuration_callback(data):
        """Run when the configuration callback is called."""
        token_url = urljoin(BASE_URL, '/oauth/token')
        oauth.fetch_token(token_url, client_secret=config[CONF_CLIENT_SECRET], code=data.get('pin_code'))
        token = oauth.token['access_token']
        save_token(hass, token)
        continue_setup_platform(hass, config, token, add_devices, discovery_info)

    if 'trakt' not in _CONFIGURING:
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
    token = load_token(hass)

    if not token:
      request_app_setup(hass, config, add_devices, discovery_info)
    else:
      continue_setup_platform(hass, config, token, add_devices, discovery_info)

def continue_setup_platform(hass, config, token, add_devices, discovery_info=None):
    """Set up the Trakt component."""
    if "trakt" in _CONFIGURING:
        hass.components.configurator.request_done(_CONFIGURING.pop("trakt"))

    add_devices([TraktMyShowCalendarSensor(hass, config, token)], True)

def load_token(hass):
    try:
        with open(hass.config.path(TOKEN_FILE)) as data_file:
            token = {}
            try:
                token = json.load(data_file)
            except ValueError as err:
                return {}
            return token
    except IOError as err:
        return {}

def save_token(hass, token):
    with open(hass.config.path(TOKEN_FILE), 'w') as data_file:
        data_file.write(json.dumps(token))

def xstr(s):
    if s is None:
        return ''
    return str(s)

class TraktMyShowCalendarSensor(Entity):
    """Representation of a Trakt My Show Calendar sensor."""

    def __init__(self, hass, config, token):
        """Initialize the sensor."""
        import trakt
        trakt.core.OAUTH_TOKEN = token
        trakt.core.CLIENT_ID = config[CONF_CLIENT_ID]
        trakt.core.CLIENT_SECRET = config[CONF_CLIENT_SECRET]
        self._hass = hass
        self._days = config[CONF_DAYS]
        self._state = None
        self._hass.data[DATA_UPCOMING] = {}
        self._name = config[CONF_NAME]
        self.update()

    def update(self):
        """Get the latest state of the sensor."""
        from trakt.calendar import MyShowCalendar
        calendar = MyShowCalendar(days=self._days)

        if not calendar:
            _LOGGER.error("Nothing in calendar")
            return False

        self._state = len(calendar)

        for show in calendar:
            if not show:
                continue

            self._hass.data[DATA_UPCOMING][xstr(show.show) + ' - ' + xstr(show.title)] = {
                "show": xstr(show.show),
                "title": xstr(show.title),
                "season": xstr(show.season),
                "number": xstr(show.number),
                "overview": xstr(show.overview),
                "airs_at": xstr(show.airs_at),
                "trakt_id": xstr(show.trakt),
                "tmdb_id": xstr(show.tmdb),
                "tvdb_id": xstr(show.tvdb),
                "imdb_id": xstr(show.imdb),
            }

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        return 'mdi:calendar'

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement this sensor expresses itself in."""
        return 'shows'

    @property
    def device_state_attributes(self):
        """Return the state attributes of the sensor."""
        return self._hass.data[DATA_UPCOMING]
