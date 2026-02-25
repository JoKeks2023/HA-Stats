"""Vibecoden HA Stats — DataUpdateCoordinator."""
from __future__ import annotations

import asyncio
import datetime
import logging
import re
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    POKEMON_NAMES,
    DEVICE_QUOTES,
    HOUSE_MASCOTS,
)

_LOGGER = logging.getLogger(__name__)

# Common emoji pattern (BMP + supplementary planes)
_EMOJI_RE = re.compile(
    "[\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F700-\U0001F77F"
    "\U0001F780-\U0001F7FF"
    "\U0001F800-\U0001F8FF"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FA6F"
    "\U0001FA70-\U0001FAFF"
    "\u2600-\u26FF"
    "\u2700-\u27BF"
    "]+",
    flags=re.UNICODE,
)


class VibeStatsCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Central coordinator that gathers all HA stats."""

    def __init__(
        self,
        hass: HomeAssistant,
        update_interval: datetime.timedelta,
        enable_fun_stats: bool = True,
        enable_host_telemetry: bool = True,
    ) -> None:
        """Initialise the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )
        self.enable_fun_stats = enable_fun_stats
        self.enable_host_telemetry = enable_host_telemetry

    # ------------------------------------------------------------------
    # Main data-fetch method
    # ------------------------------------------------------------------

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch fresh stats from Home Assistant internals."""
        try:
            core = await self._collect_core_stats()
            fun: dict[str, Any] = {}
            if self.enable_fun_stats:
                # Fun stats are CPU-light string operations — run on event loop
                fun = await asyncio.get_event_loop().run_in_executor(
                    None, self._collect_fun_stats_sync
                )
            return {"core": core, "fun": fun}
        except Exception as err:
            raise UpdateFailed(f"Error updating VibeStats data: {err}") from err

    # ------------------------------------------------------------------
    # Core stats
    # ------------------------------------------------------------------

    async def _collect_core_stats(self) -> dict[str, Any]:
        """Collect useful / actionable statistics."""
        hass = self.hass

        # ── Entity & device counts ──────────────────────────────────
        all_states = hass.states.async_all()
        total_entities: int = len(all_states)

        try:
            from homeassistant.helpers import device_registry as dr
            dev_reg = dr.async_get(hass)
            total_devices: int = len(dev_reg.devices)
        except Exception:
            _LOGGER.debug("Could not access device registry", exc_info=True)
            total_devices = 0

        # ── Integration count ────────────────────────────────────────
        integrations_count: int = len(hass.config_entries.async_entries())

        # ── Domain-specific counts ───────────────────────────────────
        automation_count: int = sum(
            1 for s in all_states if s.entity_id.startswith("automation.")
        )
        script_count: int = sum(
            1 for s in all_states if s.entity_id.startswith("script.")
        )
        scene_count: int = sum(
            1 for s in all_states if s.entity_id.startswith("scene.")
        )

        # ── Uptime (days) ─────────────────────────────────────────────
        # hass.data may carry a 'started' timestamp set at boot in newer HA
        # versions; fall back to 0 if unavailable.
        uptime_days: int = 0
        try:
            import homeassistant.util.dt as dt_util
            boot_time: datetime.datetime | None = None

            # Try getting boot time via psutil (optional)
            try:
                import psutil  # type: ignore[import]
                boot_ts = psutil.boot_time()
                boot_time = datetime.datetime.fromtimestamp(
                    boot_ts, tz=datetime.timezone.utc
                )
                _LOGGER.debug("Boot time from psutil: %s", boot_time)
            except ImportError:
                _LOGGER.debug("psutil not available — uptime will be 0")

            if boot_time is not None:
                delta = dt_util.utcnow() - boot_time
                uptime_days = max(0, delta.days)
        except Exception:
            _LOGGER.debug("Could not calculate uptime", exc_info=True)

        # ── Active devices in last 24h ────────────────────────────────
        # A device is "active" if any of its entities changed state in the last 24h.
        try:
            import homeassistant.util.dt as dt_util
            cutoff = dt_util.utcnow() - datetime.timedelta(hours=24)
            active_entities_24h: int = sum(
                1
                for s in all_states
                if s.last_changed is not None and s.last_changed >= cutoff
            )
        except Exception:
            active_entities_24h = 0

        # ── Host telemetry (CPU / RAM) ────────────────────────────────
        host_cpu_pct: float | None = None
        host_ram_pct: float | None = None

        if self.enable_host_telemetry:
            try:
                import psutil  # type: ignore[import]

                # psutil calls are blocking — push to thread pool
                def _read_psutil() -> tuple[float, float]:
                    cpu = psutil.cpu_percent(interval=0.5)
                    ram = psutil.virtual_memory().percent
                    return cpu, ram

                host_cpu_pct, host_ram_pct = await self.hass.async_add_executor_job(
                    _read_psutil
                )
                _LOGGER.debug("CPU: %.1f%% / RAM: %.1f%%", host_cpu_pct, host_ram_pct)
            except ImportError:
                _LOGGER.debug(
                    "psutil not installed — host telemetry unavailable. "
                    "Install it or disable host telemetry in options."
                )
            except Exception:
                _LOGGER.debug("Error reading host telemetry", exc_info=True)

        # ── Energy sensors (last 24 h sum) ────────────────────────────
        energy_24h_kwh: float = 0.0
        try:
            energy_24h_kwh = self._aggregate_energy(all_states)
        except Exception:
            _LOGGER.debug("Could not aggregate energy stats", exc_info=True)

        return {
            "total_entities": total_entities,
            "total_devices": total_devices,
            "integrations_count": integrations_count,
            "automation_count": automation_count,
            "script_count": script_count,
            "scene_count": scene_count,
            "uptime_days": uptime_days,
            "active_entities_24h": active_entities_24h,
            "host_cpu_pct": host_cpu_pct,
            "host_ram_pct": host_ram_pct,
            "energy_24h_kwh": energy_24h_kwh,
        }

    # ------------------------------------------------------------------
    # Fun / useless stats (runs in executor thread to keep event loop free)
    # ------------------------------------------------------------------

    def _collect_fun_stats_sync(self) -> dict[str, Any]:
        """Collect purely-for-fun statistics (synchronous, runs in executor)."""
        all_states = self.hass.states.async_all()
        entity_ids: list[str] = [s.entity_id for s in all_states]
        all_names: list[str] = []
        for s in all_states:
            name = s.attributes.get("friendly_name") or ""
            if name:
                all_names.append(name)

        # ── Average entity-ID length ─────────────────────────────────
        avg_entity_id_length: float = (
            sum(len(eid) for eid in entity_ids) / len(entity_ids)
            if entity_ids
            else 0.0
        )

        # ── Most used emoji across friendly names ─────────────────────
        emoji_counts: dict[str, int] = {}
        total_chars: int = 0
        emoji_chars: int = 0
        for name in all_names:
            total_chars += len(name)
            for match in _EMOJI_RE.finditer(name):
                emoji_chars += len(match.group())
                for ch in match.group():
                    emoji_counts[ch] = emoji_counts.get(ch, 0) + 1

        most_used_emoji: str = (
            max(emoji_counts, key=lambda e: emoji_counts[e])
            if emoji_counts
            else "🤷"
        )
        emoji_density: float = (
            round(emoji_chars / total_chars * 100, 2) if total_chars > 0 else 0.0
        )

        # ── Devices named after Pokémon ───────────────────────────────
        pokemon_count: int = sum(
            1
            for name in all_names
            if any(pokemon in name.lower() for pokemon in POKEMON_NAMES)
        )

        # ── Most redundant name (shortest name repeated most times) ───
        name_freq: dict[str, int] = {}
        for name in all_names:
            clean = name.strip().lower()
            if clean:
                name_freq[clean] = name_freq.get(clean, 0) + 1

        most_redundant_name: str = "N/A"
        if name_freq:
            # Sort by frequency desc, then by shortest name
            best = max(name_freq, key=lambda n: (name_freq[n], -len(n)))
            if name_freq[best] > 1:
                most_redundant_name = f"{best!r} (×{name_freq[best]})"

        # ── Daily rotating quotes / mascots ──────────────────────────
        day_of_year: int = datetime.date.today().timetuple().tm_yday
        random_daily_quote: str = DEVICE_QUOTES[day_of_year % len(DEVICE_QUOTES)]
        house_mascot: str = HOUSE_MASCOTS[day_of_year % len(HOUSE_MASCOTS)]

        return {
            "most_used_emoji": most_used_emoji,
            "avg_entity_id_length": round(avg_entity_id_length, 2),
            "devices_named_after_pokemon": pokemon_count,
            "emoji_density": emoji_density,
            "most_redundant_name": most_redundant_name,
            "random_daily_quote": random_daily_quote,
            "house_mascot": house_mascot,
            # Boolean facts used by binary sensors
            "everything_off": self._check_everything_off(),
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _aggregate_energy(self, all_states: list[Any]) -> float:
        """Sum the state values of all energy sensors (kWh)."""
        total: float = 0.0
        for state in all_states:
            unit = state.attributes.get("unit_of_measurement", "")
            if unit.lower() in ("kwh", "wh") and state.state not in (
                "unavailable",
                "unknown",
                "",
                None,
            ):
                try:
                    value = float(state.state)
                    if unit.lower() == "wh":
                        value /= 1000.0
                    total += value
                except ValueError:
                    pass
        return round(total, 3)

    def _check_everything_off(self) -> bool:
        """Return True if no light entity is currently 'on'."""
        return not any(
            s.state == "on"
            for s in self.hass.states.async_all()
            if s.entity_id.startswith("light.")
        )
