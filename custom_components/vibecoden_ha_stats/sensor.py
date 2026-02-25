"""Sensor platform for Vibecoden HA Stats."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfEnergy, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import VibeStatsCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class VibeSensorDescription(SensorEntityDescription):
    """Extended sensor description with data path helpers."""

    # "core" or "fun"
    data_section: str = "core"
    # key inside the section dict
    data_key: str = ""


# ── Core sensors ────────────────────────────────────────────────────────────

CORE_SENSORS: tuple[VibeSensorDescription, ...] = (
    VibeSensorDescription(
        key="vibe_total_devices",
        name="Total Devices",
        icon="mdi:devices",
        native_unit_of_measurement=None,
        state_class=SensorStateClass.MEASUREMENT,
        data_section="core",
        data_key="total_devices",
    ),
    VibeSensorDescription(
        key="vibe_total_entities",
        name="Total Entities",
        icon="mdi:format-list-bulleted",
        native_unit_of_measurement=None,
        state_class=SensorStateClass.MEASUREMENT,
        data_section="core",
        data_key="total_entities",
    ),
    VibeSensorDescription(
        key="vibe_integrations_count",
        name="Integrations Count",
        icon="mdi:puzzle",
        native_unit_of_measurement=None,
        state_class=SensorStateClass.MEASUREMENT,
        data_section="core",
        data_key="integrations_count",
    ),
    VibeSensorDescription(
        key="vibe_automation_count",
        name="Automation Count",
        icon="mdi:robot",
        native_unit_of_measurement=None,
        state_class=SensorStateClass.MEASUREMENT,
        data_section="core",
        data_key="automation_count",
    ),
    VibeSensorDescription(
        key="vibe_uptime_days",
        name="Uptime Days",
        icon="mdi:timer-outline",
        native_unit_of_measurement=UnitOfTime.DAYS,
        state_class=SensorStateClass.MEASUREMENT,
        data_section="core",
        data_key="uptime_days",
    ),
    VibeSensorDescription(
        key="vibe_active_devices_24h",
        name="Active Entities (24 h)",
        icon="mdi:pulse",
        native_unit_of_measurement=None,
        state_class=SensorStateClass.MEASUREMENT,
        data_section="core",
        data_key="active_entities_24h",
    ),
    VibeSensorDescription(
        key="vibe_host_cpu_pct",
        name="Host CPU Usage",
        icon="mdi:cpu-64-bit",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        data_section="core",
        data_key="host_cpu_pct",
    ),
    VibeSensorDescription(
        key="vibe_host_ram_pct",
        name="Host RAM Usage",
        icon="mdi:memory",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        data_section="core",
        data_key="host_ram_pct",
    ),
    VibeSensorDescription(
        key="vibe_energy_24h_kwh",
        name="Energy (24 h)",
        icon="mdi:lightning-bolt",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.MEASUREMENT,
        data_section="core",
        data_key="energy_24h_kwh",
    ),
    VibeSensorDescription(
        key="vibe_script_count",
        name="Script Count",
        icon="mdi:script-text",
        native_unit_of_measurement=None,
        state_class=SensorStateClass.MEASUREMENT,
        data_section="core",
        data_key="script_count",
    ),
    VibeSensorDescription(
        key="vibe_scene_count",
        name="Scene Count",
        icon="mdi:palette",
        native_unit_of_measurement=None,
        state_class=SensorStateClass.MEASUREMENT,
        data_section="core",
        data_key="scene_count",
    ),
)

# ── Fun sensors ─────────────────────────────────────────────────────────────

FUN_SENSORS: tuple[VibeSensorDescription, ...] = (
    VibeSensorDescription(
        key="vibe_most_used_emoji",
        name="Most Used Emoji",
        icon="mdi:emoticon-outline",
        data_section="fun",
        data_key="most_used_emoji",
    ),
    VibeSensorDescription(
        key="vibe_avg_entity_id_length",
        name="Avg Entity ID Length",
        icon="mdi:ruler",
        native_unit_of_measurement="chars",
        state_class=SensorStateClass.MEASUREMENT,
        data_section="fun",
        data_key="avg_entity_id_length",
    ),
    VibeSensorDescription(
        key="vibe_devices_named_after_pokemon",
        name="Devices Named After Pokémon",
        icon="mdi:pokeball",
        native_unit_of_measurement=None,
        state_class=SensorStateClass.MEASUREMENT,
        data_section="fun",
        data_key="devices_named_after_pokemon",
    ),
    VibeSensorDescription(
        key="vibe_emoji_density",
        name="Emoji Density",
        icon="mdi:percent",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        data_section="fun",
        data_key="emoji_density",
    ),
    VibeSensorDescription(
        key="vibe_most_redundant_name",
        name="Most Redundant Name",
        icon="mdi:content-duplicate",
        data_section="fun",
        data_key="most_redundant_name",
    ),
    VibeSensorDescription(
        key="vibe_random_daily_device_quote",
        name="Random Daily Device Quote",
        icon="mdi:comment-quote",
        data_section="fun",
        data_key="random_daily_quote",
    ),
    VibeSensorDescription(
        key="vibe_house_mascot",
        name="House Mascot",
        icon="mdi:home-heart",
        data_section="fun",
        data_key="house_mascot",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor entities from a config entry."""
    coordinator: VibeStatsCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[VibeSensor] = []

    for description in CORE_SENSORS:
        entities.append(VibeSensor(coordinator, entry, description))

    if coordinator.enable_fun_stats:
        for description in FUN_SENSORS:
            entities.append(VibeSensor(coordinator, entry, description))

    async_add_entities(entities)


class VibeSensor(CoordinatorEntity[VibeStatsCoordinator], SensorEntity):
    """A single Vibecoden HA Stats sensor."""

    entity_description: VibeSensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: VibeStatsCoordinator,
        entry: ConfigEntry,
        description: VibeSensorDescription,
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
            entry_type="service",  # type: ignore[arg-type]
        )

    @property
    def native_value(self) -> Any:
        """Return the current sensor value."""
        section = self.entity_description.data_section
        key = self.entity_description.data_key
        data: dict[str, Any] = self.coordinator.data or {}
        value = data.get(section, {}).get(key)
        _LOGGER.debug("Sensor %s value: %s", self.entity_description.key, value)
        return value
