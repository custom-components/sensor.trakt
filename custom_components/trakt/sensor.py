"""Sensor platform for Trakt."""

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_CLIENT_ID, CONF_NAME
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION
from .coordinator import TraktDataUpdateCoordinator
from .oauth_impl import HomeAssistant


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up device tracker for Mikrotik component."""
    coordinator: TraktDataUpdateCoordinator = config_entry.runtime_data
    async_add_entities([TraktUpcomingCalendarSensor(coordinator)])


class TraktUpcomingCalendarSensor(
    CoordinatorEntity[TraktDataUpdateCoordinator], SensorEntity
):
    """Representation of a Trakt Upcoming Calendar sensor."""

    _attr_icon = "mdi:calendar"
    _attr_native_unit_of_measurement = "shows"
    _attr_attribution = ATTRIBUTION

    def __init__(self, coordinator: TraktDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = coordinator.config_entry.data[CONF_NAME]
        self._attr_unique_id = coordinator.config_entry.data[CONF_CLIENT_ID]

    @property
    def state(self) -> int:
        """Return the state of the sensor."""
        return len(self.coordinator.tv_shows)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes of the sensor."""
        return {"data": self.coordinator.data}
