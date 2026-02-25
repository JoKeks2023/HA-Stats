"""Config flow & options flow for Vibecoden HA Stats."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    CONF_ENABLE_FUN_STATS,
    CONF_ENABLE_HOST_TELEMETRY,
    CONF_SCAN_INTERVAL,
    DEFAULT_ENABLE_FUN_STATS,
    DEFAULT_ENABLE_HOST_TELEMETRY,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)


class VibeStatsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the initial config flow (one-shot setup — no user input needed)."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Handle the user step."""
        # Only allow a single instance
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            return self.async_create_entry(title="Vibecoden HA Stats", data={})

        return self.async_show_form(step_id="user")

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> "VibeStatsOptionsFlow":
        """Return the options flow handler."""
        return VibeStatsOptionsFlow(config_entry)


class VibeStatsOptionsFlow(config_entries.OptionsFlow):
    """Handle options for Vibecoden HA Stats."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialise."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Manage the options."""
        current = self._config_entry.options

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=current.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                ): vol.All(vol.Coerce(int), vol.Range(min=30, max=86400)),
                vol.Optional(
                    CONF_ENABLE_FUN_STATS,
                    default=current.get(CONF_ENABLE_FUN_STATS, DEFAULT_ENABLE_FUN_STATS),
                ): bool,
                vol.Optional(
                    CONF_ENABLE_HOST_TELEMETRY,
                    default=current.get(
                        CONF_ENABLE_HOST_TELEMETRY, DEFAULT_ENABLE_HOST_TELEMETRY
                    ),
                ): bool,
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
