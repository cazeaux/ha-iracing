"""Support for the Brother service."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
import logging
from typing import Any

from homeassistant.components.sensor import (
    DOMAIN as PLATFORM,
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, PERCENTAGE, EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import IracingDataUpdateCoordinator
from .const import DOMAIN, DATA_CONFIG_ENTRY

_LOGGER = logging.getLogger(__name__)


@dataclass
class IracingSensorRequiredKeysMixin:
    """Class for Brother entity required keys."""

    value: Callable[[any], StateType | datetime]


@dataclass
class IracingSensorEntityDescription(
    SensorEntityDescription, IracingSensorRequiredKeysMixin
):
    """A class that describes sensor entities."""

    attr_fn: Callable[[dict[str, Any]], dict[str, Any]] = lambda _: {}


SENSOR_TYPES: tuple[IracingSensorEntityDescription, ...] = (
    IracingSensorEntityDescription(
        key="driver",
        icon="",
        translation_key="driver",
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda data: data["name"],
        attr_fn=lambda data: data["recent_results"],
    ),
    ### ROAD
    IracingSensorEntityDescription(
        key="road_licence_ir",
        icon="",
        translation_key="road_licence_ir",
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda data: data["road_licence_ir"],
    ),
    IracingSensorEntityDescription(
        key="road_licence_sr",
        icon="",
        translation_key="road_licence_sr",
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda data: data["road_licence_sr"],
    ),
    IracingSensorEntityDescription(
        key="road_starts",
        icon="",
        translation_key="road_starts",
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda data: data["road_starts"],
    ),
    IracingSensorEntityDescription(
        key="road_laps",
        icon="",
        translation_key="road_laps",
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda data: data["road_laps"],
    ),
    IracingSensorEntityDescription(
        key="road_wins",
        icon="",
        translation_key="road_wins",
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda data: data["road_wins"],
    ),
    IracingSensorEntityDescription(
        key="road_top5",
        icon="",
        translation_key="road_top5",
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda data: data["road_top5"],
    ),
    ### DIRT ROAD
    IracingSensorEntityDescription(
        key="oval_licence_ir",
        icon="",
        translation_key="dirt_road_licence_ir",
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda data: data["dirt_road_licence_ir"],
    ),
    IracingSensorEntityDescription(
        key="dirt_road_licence_sr",
        icon="",
        translation_key="dirt_road_licence_sr",
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda data: data["dirt_road_licence_sr"],
    ),
    IracingSensorEntityDescription(
        key="dirt_road_starts",
        icon="",
        translation_key="dirt_road_starts",
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda data: data["dirt_road_starts"],
    ),
    IracingSensorEntityDescription(
        key="dirt_road_laps",
        icon="",
        translation_key="dirt_road_laps",
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda data: data["dirt_road_laps"],
    ),
    IracingSensorEntityDescription(
        key="dirt_road_wins",
        icon="",
        translation_key="dirt_road_wins",
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda data: data["dirt_road_wins"],
    ),
    IracingSensorEntityDescription(
        key="dirt_road_top5",
        icon="",
        translation_key="dirt_road_top5",
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda data: data["dirt_road_top5"],
    ),
    ### OVAL
    IracingSensorEntityDescription(
        key="oval_licence_ir",
        icon="",
        translation_key="oval_licence_ir",
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda data: data["oval_licence_ir"],
    ),
    IracingSensorEntityDescription(
        key="oval_licence_sr",
        icon="",
        translation_key="oval_licence_sr",
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda data: data["oval_licence_sr"],
    ),
    IracingSensorEntityDescription(
        key="oval_starts",
        icon="",
        translation_key="oval_starts",
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda data: data["oval_starts"],
    ),
    IracingSensorEntityDescription(
        key="oval_laps",
        icon="",
        translation_key="oval_laps",
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda data: data["oval_laps"],
    ),
    IracingSensorEntityDescription(
        key="oval_wins",
        icon="",
        translation_key="oval_wins",
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda data: data["oval_wins"],
    ),
    IracingSensorEntityDescription(
        key="oval_top5",
        icon="",
        translation_key="oval_top5",
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda data: data["oval_top5"],
    ),
    ### DIRT OVAL
    IracingSensorEntityDescription(
        key="dirt_oval_licence_ir",
        icon="",
        translation_key="dirt_oval_licence_ir",
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda data: data["dirt_oval_licence_ir"],
    ),
    IracingSensorEntityDescription(
        key="dirt_oval_licence_sr",
        icon="",
        translation_key="dirt_oval_licence_sr",
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda data: data["dirt_oval_licence_sr"],
    ),
    IracingSensorEntityDescription(
        key="dirt_oval_starts",
        icon="",
        translation_key="dirt_oval_starts",
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda data: data["dirt_oval_starts"],
    ),
    IracingSensorEntityDescription(
        key="dirt_oval_laps",
        icon="",
        translation_key="dirt_oval_laps",
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda data: data["dirt_oval_laps"],
    ),
    IracingSensorEntityDescription(
        key="dirt_oval_wins",
        icon="",
        translation_key="dirt_oval_wins",
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda data: data["dirt_oval_wins"],
    ),
    IracingSensorEntityDescription(
        key="dirt_oval_top5",
        icon="",
        translation_key="dirt_oval_top5",
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda data: data["dirt_oval_top5"],
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Add iRacing entities from a config_entry."""
    coordinator = hass.data[DOMAIN][DATA_CONFIG_ENTRY][entry.entry_id]

    await coordinator.async_config_entry_first_refresh()

    sensors = []
    device_info = DeviceInfo(
        identifiers={(DOMAIN, coordinator.data["cust_id"])},
        entry_type=DeviceEntryType.SERVICE,
        manufacturer="iRacing.com",
        model=coordinator.data["name"],
        name=coordinator.data["name"],
    )

    for description in SENSOR_TYPES:
        if description.value(coordinator.data) is not None:
            sensors.append(IracingSensor(coordinator, description, device_info))
    async_add_entities(sensors, False)


class IracingSensor(CoordinatorEntity[IracingDataUpdateCoordinator], SensorEntity):
    """Define an iRacing sensor."""

    _attr_has_entity_name = True
    entity_description: IracingSensorEntityDescription

    def __init__(
        self,
        coordinator: IracingDataUpdateCoordinator,
        description: IracingSensorEntityDescription,
        device_info: DeviceInfo,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._attr_device_info = device_info
        self._attr_native_value = description.value(coordinator.data)
        self._attr_unique_id = f"{coordinator.data['cust_id']}_{description.key}"
        self.entity_description = description

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_native_value = self.entity_description.value(self.coordinator.data)
        self.async_write_ha_state()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        _LOGGER.info(self.coordinator.data)
        return self.entity_description.attr_fn(self.coordinator.data)
