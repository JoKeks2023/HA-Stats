"""Binary sensor platform for Vibecoden HA Stats."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import VibeStatsCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class VibeBinarySensorDescription(BinarySensorEntityDescription):
    """Binary sensor description with data path helpers."""

    data_section: str = "fun"
    data_key: str = ""


BINARY_SENSORS: tuple[VibeBinarySensorDescription, ...] = (
    VibeBinarySensorDescription(
        key="vibe_everything_off_party_mode",
        name="Everything Off (Party Mode)",
        icon="mdi:party-popper",
        data_section="fun",
        data_key="everything_off",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensor entities from a config entry."""
    coordinator: VibeStatsCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[VibeBinarySensor] = []
    if coordinator.enable_fun_stats:
        for description in BINARY_SENSORS:
            entities.append(VibeBinarySensor(coordinator, entry, description))

    async_add_entities(entities)


class VibeBinarySensor(CoordinatorEntity[VibeStatsCoordinator], BinarySensorEntity):
    """A single Vibecoden HA Stats binary sensor."""

    entity_description: VibeBinarySensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: VibeStatsCoordinator,
        entry: ConfigEntry,
        description: VibeBinarySensorDescription,
    ) -> None:
        """Initialise."""
        super().__init__(coordinator)
        self.entity_description = description
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Vibecoden HA Stats",
            manufacturer="Vibecoden",
            model="HA Stats",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def is_on(self) -> bool | None:
        """Return True when the condition is active."""
        section = self.entity_description.data_section
        key = self.entity_description.data_key
        data: dict[str, Any] = self.coordinator.data or {}
        value = data.get(section, {}).get(key)
        _LOGGER.debug(
            "Binary sensor %s value: %s", self.entity_description.key, value
        )
        if value is None:
            return None
        return bool(value)
