"""Sensor platform for Trakt"""
from homeassistant.const import ATTR_ATTRIBUTION, CONF_NAME, CONF_CLIENT_ID

from homeassistant.helpers.entity import Entity

from .const import ATTRIBUTION, DOMAIN


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up device tracker for Mikrotik component."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([TraktUpcomingCalendarSensor(coordinator)], True)


class TraktUpcomingCalendarSensor(Entity):
    """Representation of a Trakt Upcoming Calendar sensor."""

    def __init__(self, coordinator):
        """Initialize the sensor."""
        self.coordinator = coordinator
        self._name = coordinator.config_entry.data[CONF_NAME]

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def unique_id(self):
        """Return the unique id of the entity."""
        return self.coordinator.config_entry.data[CONF_CLIENT_ID]

    @property
    def should_poll(self):
        """Disable polling."""
        return False

    @property
    def state(self):
        """Return the state of the sensor."""
        return len(self.coordinator.calendar) if self.coordinator.calendar else 0

    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        return "mdi:calendar"

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement this sensor expresses itself in."""
        return "shows"

    @property
    def device_state_attributes(self):
        """Return the state attributes of the sensor."""
        attributes = {
            "data": self.coordinator.data,
            ATTR_ATTRIBUTION: ATTRIBUTION,
        }

        return attributes

    async def async_added_to_hass(self):
        """Handle entity which will be added."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )

    async def async_update(self):
        """Request coordinator to update data."""
        await self.coordinator.async_request_refresh()
