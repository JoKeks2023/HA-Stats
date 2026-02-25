"""Sensor platform for Vibecoden HA Stats."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfEnergy, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
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
    # optional extra attributes key → coordinator data keys mapping
    # e.g. {"domain_breakdown": "domain_counts"}
    extra_attrs: dict[str, str] | None = None


# ── Core sensors ────────────────────────────────────────────────────────────

CORE_SENSORS: tuple[VibeSensorDescription, ...] = (
    VibeSensorDescription(
        key="vibe_total_devices",
        name="Total Devices",
        icon="mdi:devices",
        state_class=SensorStateClass.MEASUREMENT,
        data_section="core",
        data_key="total_devices",
    ),
    VibeSensorDescription(
        key="vibe_total_entities",
        name="Total Entities",
        icon="mdi:format-list-bulleted",
        state_class=SensorStateClass.MEASUREMENT,
        data_section="core",
        data_key="total_entities",
        extra_attrs={"domain_breakdown": "domain_counts"},
    ),
    VibeSensorDescription(
        key="vibe_integrations_count",
        name="Integrations Count",
        icon="mdi:puzzle",
        state_class=SensorStateClass.MEASUREMENT,
        data_section="core",
        data_key="integrations_count",
    ),
    VibeSensorDescription(
        key="vibe_automation_count",
        name="Automation Count",
        icon="mdi:robot",
        state_class=SensorStateClass.MEASUREMENT,
        data_section="core",
        data_key="automation_count",
    ),
    VibeSensorDescription(
        key="vibe_script_count",
        name="Script Count",
        icon="mdi:script-text",
        state_class=SensorStateClass.MEASUREMENT,
        data_section="core",
        data_key="script_count",
    ),
    VibeSensorDescription(
        key="vibe_scene_count",
        name="Scene Count",
        icon="mdi:palette",
        state_class=SensorStateClass.MEASUREMENT,
        data_section="core",
        data_key="scene_count",
    ),
    VibeSensorDescription(
        key="vibe_light_count",
        name="Light Count",
        icon="mdi:lightbulb-multiple",
        state_class=SensorStateClass.MEASUREMENT,
        data_section="core",
        data_key="light_count",
    ),
    VibeSensorDescription(
        key="vibe_switch_count",
        name="Switch Count",
        icon="mdi:toggle-switch",
        state_class=SensorStateClass.MEASUREMENT,
        data_section="core",
        data_key="switch_count",
    ),
    VibeSensorDescription(
        key="vibe_binary_sensor_count",
        name="Binary Sensor Count",
        icon="mdi:radiobox-marked",
        state_class=SensorStateClass.MEASUREMENT,
        data_section="core",
        data_key="binary_sensor_count",
    ),
    VibeSensorDescription(
        key="vibe_sensor_count",
        name="Sensor Count",
        icon="mdi:thermometer",
        state_class=SensorStateClass.MEASUREMENT,
        data_section="core",
        data_key="sensor_count",
    ),
    VibeSensorDescription(
        key="vibe_person_count",
        name="Person Count",
        icon="mdi:account-group",
        state_class=SensorStateClass.MEASUREMENT,
        data_section="core",
        data_key="person_count",
    ),
    VibeSensorDescription(
        key="vibe_camera_count",
        name="Camera Count",
        icon="mdi:cctv",
        state_class=SensorStateClass.MEASUREMENT,
        data_section="core",
        data_key="camera_count",
    ),
    VibeSensorDescription(
        key="vibe_media_player_count",
        name="Media Player Count",
        icon="mdi:speaker",
        state_class=SensorStateClass.MEASUREMENT,
        data_section="core",
        data_key="media_player_count",
    ),
    VibeSensorDescription(
        key="vibe_cover_count",
        name="Cover Count",
        icon="mdi:window-shutter",
        state_class=SensorStateClass.MEASUREMENT,
        data_section="core",
        data_key="cover_count",
    ),
    VibeSensorDescription(
        key="vibe_climate_count",
        name="Climate Count",
        icon="mdi:thermostat",
        state_class=SensorStateClass.MEASUREMENT,
        data_section="core",
        data_key="climate_count",
    ),
    VibeSensorDescription(
        key="vibe_unique_domains_count",
        name="Unique Domains",
        icon="mdi:tag-multiple",
        state_class=SensorStateClass.MEASUREMENT,
        data_section="core",
        data_key="unique_domains_count",
    ),
    VibeSensorDescription(
        key="vibe_unavailable_count",
        name="Unavailable Entities",
        icon="mdi:alert-circle-outline",
        state_class=SensorStateClass.MEASUREMENT,
        data_section="core",
        data_key="unavailable_count",
    ),
    VibeSensorDescription(
        key="vibe_unknown_count",
        name="Unknown State Entities",
        icon="mdi:help-circle-outline",
        state_class=SensorStateClass.MEASUREMENT,
        data_section="core",
        data_key="unknown_count",
    ),
    VibeSensorDescription(
        key="vibe_disabled_entities",
        name="Disabled Entities",
        icon="mdi:eye-off-outline",
        state_class=SensorStateClass.MEASUREMENT,
        data_section="core",
        data_key="disabled_entities",
    ),
    VibeSensorDescription(
        key="vibe_lights_on",
        name="Lights Currently On",
        icon="mdi:lightbulb-on",
        state_class=SensorStateClass.MEASUREMENT,
        data_section="core",
        data_key="lights_on",
    ),
    VibeSensorDescription(
        key="vibe_uptime_days",
        name="Uptime (Days)",
        icon="mdi:timer-outline",
        native_unit_of_measurement=UnitOfTime.DAYS,
        state_class=SensorStateClass.MEASUREMENT,
        data_section="core",
        data_key="uptime_days",
    ),
    VibeSensorDescription(
        key="vibe_uptime_hours",
        name="Uptime (Hours)",
        icon="mdi:clock-outline",
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.MEASUREMENT,
        data_section="core",
        data_key="uptime_hours",
    ),
    VibeSensorDescription(
        key="vibe_active_devices_24h",
        name="Active Entities (24 h)",
        icon="mdi:pulse",
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
        key="vibe_host_disk_pct",
        name="Host Disk Usage",
        icon="mdi:harddisk",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        data_section="core",
        data_key="host_disk_pct",
    ),
    VibeSensorDescription(
        key="vibe_energy_24h_kwh",
        name="Energy Total (kWh)",
        icon="mdi:lightning-bolt",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.MEASUREMENT,
        data_section="core",
        data_key="energy_24h_kwh",
        extra_attrs={"contributing_sensors": "energy_entity_count"},
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
        extra_attrs={
            "longest_entity_id": "longest_entity_id",
            "shortest_entity_id": "shortest_entity_id",
        },
    ),
    VibeSensorDescription(
        key="vibe_devices_named_after_pokemon",
        name="Devices Named After Pokémon",
        icon="mdi:pokeball",
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
        key="vibe_names_with_numbers",
        name="Entity Names Containing Numbers",
        icon="mdi:numeric",
        state_class=SensorStateClass.MEASUREMENT,
        data_section="fun",
        data_key="names_with_numbers",
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
            entry_type=DeviceEntryType.SERVICE,
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

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra state attributes if defined in the description."""
        extra_attrs = self.entity_description.extra_attrs
        if not extra_attrs:
            return None
        section = self.entity_description.data_section
        data: dict[str, Any] = self.coordinator.data or {}
        section_data = data.get(section, {})
        return {
            attr_name: section_data.get(data_key)
            for attr_name, data_key in extra_attrs.items()
        }
