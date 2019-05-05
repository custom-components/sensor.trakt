"""Sensor platform for Trakt"""
import json
import logging
import time
from datetime import datetime, timedelta

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.entity import Entity

__version__ = '1.0.1'

REQUIREMENTS = ['trakt==2.8.2', 'requests_oauthlib==1.0.0']

BASE_URL = 'https://api-v2launch.trakt.tv/'
CONF_CLIENT_ID = 'id'
CONF_CLIENT_SECRET = 'secret'
CONF_DAYS = 'days'
CONF_EXCLUDE = 'exclude'
CONF_NAME = 'name'
CONF_USERNAME = 'username'
DATA_UPCOMING = 'trakt_upcoming'
REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'
SCAN_INTERVAL = timedelta(minutes=30)
TOKEN_FILE = '.trakt.conf'

LIST_SCHEMA = vol.Schema([str])

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_CLIENT_ID): cv.string,
    vol.Required(CONF_CLIENT_SECRET): cv.string,
    vol.Required(CONF_USERNAME): cv.string,
    vol.Optional(CONF_DAYS, default=30): cv.positive_int,
    vol.Optional(CONF_NAME, default='Trakt Upcoming Calendar'): cv.string,
    vol.Optional(CONF_EXCLUDE, default=[]): LIST_SCHEMA,
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

    add_devices([TraktUpcomingCalendarSensor(hass, config, token)], True)


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


class TraktUpcomingCalendarSensor(Entity):
    """Representation of a Trakt Upcoming Calendar sensor."""

    def __init__(self, hass, config, token):
        """Initialize the sensor."""
        import trakt
        from pytz import timezone
        self._tz = timezone(str(hass.config.time_zone))
        trakt.core.OAUTH_TOKEN = token
        trakt.core.CLIENT_ID = config[CONF_CLIENT_ID]
        trakt.core.CLIENT_SECRET = config[CONF_CLIENT_SECRET]
        self._hass = hass
        self._days = config[CONF_DAYS]
        self._state = None
        self._hass.data[DATA_UPCOMING] = {}
        self._name = config[CONF_NAME]
        self._exclude = config[CONF_EXCLUDE]
        self.update()

    def update(self):
        """Get the latest state of the sensor."""
        from trakt.calendar import MyShowCalendar
        from trakt.tv import TVShow
        import requests
        attributes = {}
        default = {}
        card_json = []
        default['title_default'] = '$title'
        default['line1_default'] = '$episode'
        default['line2_default'] = '$release'
        default['line3_default'] = '$rating - $runtime'
        default['line4_default'] = '$number - $studio'
        default['icon'] = 'mdi:arrow-down-bold'
        card_json.append(default)
        calendar = MyShowCalendar(days=self._days)

        if not calendar:
            _LOGGER.error("Nothing in upcoming calendar")
            return False

        self._state = len(calendar)

        for show in calendar:
            if not show or show.show in self._exclude:
                continue

            try:
                show_details = TVShow.search(show.show, show.year)
            except AttributeError:
                _LOGGER.error('Unable to retrieve show details for ' + show.show)

            if not show_details:
                continue

            session = requests.Session()
            try:
                tmdb_url = session.get('http://api.tmdb.org/3/tv/{}?api_key=0eee347e2333d7a97b724106353ca42f'.format(
                    str(show_details[0].tmdb)))
                tmdb_json = tmdb_url.json()
            except requests.exceptions.RequestException as e:
                _LOGGER.warning('api.themoviedb.org is not responding')
                return
            image_url = 'https://image.tmdb.org/t/p/w%s%s'
            if days_until(show.airs_at.isoformat() + 'Z', self._tz) < 0:  
                continue
            if days_until(show.airs_at.isoformat() + 'Z', self._tz) <= 7:
                release = '$day, $time'
            else:
                release = '$day, $date $time'
            
            card_item = {
                'airdate': show.airs_at.isoformat() + 'Z',
                'release': release,
                'flag': False,
                'title': show.show,
                'episode': show.title,
                'number': 'S' + str(show.season) + 'E' + str(show.number),
                'rating': tmdb_json.get('vote_average', ''),
                'poster': image_url % ('500', tmdb_json.get('poster_path', '')),
                'fanart': image_url % ('780', tmdb_json.get('backdrop_path', '')),
                'runtime': tmdb_json.get('episode_run_time')[0] if len(tmdb_json.get('episode_run_time', [])) > 0 else '',
                'studio': tmdb_json.get('networks')[0].get('name', '') if len(tmdb_json.get('networks', [])) > 0 else ''
            }
            card_json.append(card_item)

        attributes['data'] = json.dumps(card_json)
        self._hass.data[DATA_UPCOMING] = attributes

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


def days_until(date, tz):
    from pytz import utc
    date = datetime.strptime(date, '%Y-%m-%dT%H:%M:%SZ')
    date = str(date.replace(tzinfo=utc).astimezone(tz))[:10]
    date = time.strptime(date, '%Y-%m-%d')
    date = time.mktime(date)
    now = datetime.now().strftime('%Y-%m-%d')
    now = time.strptime(now, '%Y-%m-%d')
    now = time.mktime(now)
    return int((date - now) / 86400)
