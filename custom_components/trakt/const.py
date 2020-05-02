"""Constants used in the Trakt integration."""
DOMAIN = "trakt"

OAUTH2_AUTHORIZE = "https://api-v2launch.trakt.tv/oauth/authorize"
OAUTH2_TOKEN = "https://api-v2launch.trakt.tv/oauth/token"

ATTRIBUTION = "Data provided by trakt.tv"

CONF_DAYS = "days"
CONF_EXCLUDE = "exclude"

DATA_UPDATED = "trakt_data_updated"

DEFAULT_DAYS = 30
DEFAULT_SCAN_INTERVAL = 60
DEFAULT_NAME = "Trakt Upcoming Calendar"

CARD_DEFAULT = {
    "title_default": "$title",
    "line1_default": "$episode",
    "line2_default": "$release",
    "line3_default": "$rating - $runtime",
    "line4_default": "$number - $studio",
    "icon": "mdi:arrow-down-bold",
}
