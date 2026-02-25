"""Vibecoden HA Stats — integration setup."""
from __future__ import annotations

import datetime
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_ENABLE_FUN_STATS,
    CONF_ENABLE_HOST_TELEMETRY,
    CONF_SCAN_INTERVAL,
    DEFAULT_ENABLE_FUN_STATS,
    DEFAULT_ENABLE_HOST_TELEMETRY,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import VibeStatsCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Vibecoden HA Stats from a config entry."""
    _LOGGER.info("Setting up Vibecoden HA Stats integration (entry: %s)", entry.entry_id)

    options: dict[str, Any] = entry.options
    scan_interval = datetime.timedelta(
        seconds=options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    )
    enable_fun = options.get(CONF_ENABLE_FUN_STATS, DEFAULT_ENABLE_FUN_STATS)
    enable_host = options.get(CONF_ENABLE_HOST_TELEMETRY, DEFAULT_ENABLE_HOST_TELEMETRY)

    coordinator = VibeStatsCoordinator(
        hass,
        update_interval=scan_interval,
        enable_fun_stats=enable_fun,
        enable_host_telemetry=enable_host,
    )

    # Perform an initial data refresh so entities have data on first load
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Reload integration when options change (new scan interval etc.)
    entry.async_on_unload(entry.add_update_listener(_async_options_update))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def _async_options_update(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update by reloading the entry."""
    _LOGGER.debug("Options updated — reloading Vibecoden HA Stats entry")
    await hass.config_entries.async_reload(entry.entry_id)
