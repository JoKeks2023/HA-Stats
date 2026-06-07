"""Vibecoden HA Stats — DataUpdateCoordinator."""
from __future__ import annotations

import datetime
import logging
import re
from typing import Any

from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.storage import Store
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
        self._store: Store[dict[str, Any]] = Store(hass, 1, f"{DOMAIN}_meta")
        self._store_loaded = False
        self._instance_first_seen_utc: datetime.datetime | None = None
        self._max_devices_ever = 0

    # ------------------------------------------------------------------
    # Main data-fetch method
    # ------------------------------------------------------------------

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch fresh stats from Home Assistant internals."""
        try:
            await self._async_load_meta_once()
            core = await self._collect_core_stats()
            fun: dict[str, Any] = {}
            if self.enable_fun_stats:
                # Capture states on the event loop before handing off to a thread.
                # hass.states.async_all() is NOT thread-safe and must only be
                # called from the event loop.
                all_states = self.hass.states.async_all()
                everything_off = not any(
                    s.state == "on"
                    for s in all_states
                    if s.entity_id.startswith("light.")
                )
                # CPU-light string operations — run in executor to avoid
                # blocking the event loop.
                fun = await self.hass.async_add_executor_job(
                    self._collect_fun_stats_sync, all_states, everything_off
                )
            return {"core": core, "fun": fun}
        except Exception as err:
            raise UpdateFailed(f"Error updating VibeStats data: {err}") from err

    async def _async_load_meta_once(self) -> None:
        """Load persistent meta information once per coordinator lifetime."""
        if self._store_loaded:
            return

        self._store_loaded = True
        try:
            saved = await self._store.async_load() or {}
            first_seen_raw = saved.get("instance_first_seen_utc")
            if isinstance(first_seen_raw, str):
                try:
                    parsed = datetime.datetime.fromisoformat(first_seen_raw)
                    if parsed.tzinfo is None:
                        parsed = parsed.replace(tzinfo=datetime.timezone.utc)
                    self._instance_first_seen_utc = parsed.astimezone(
                        datetime.timezone.utc
                    )
                except ValueError:
                    _LOGGER.debug("Invalid stored instance_first_seen_utc: %s", first_seen_raw)

            max_devices = saved.get("max_devices_ever")
            if isinstance(max_devices, int) and max_devices >= 0:
                self._max_devices_ever = max_devices
        except Exception:
            _LOGGER.debug("Could not load persistent stats meta", exc_info=True)

    async def _async_save_meta(self) -> None:
        """Persist meta information used across restarts."""
        try:
            await self._store.async_save(
                {
                    "instance_first_seen_utc": (
                        self._instance_first_seen_utc.isoformat()
                        if self._instance_first_seen_utc
                        else None
                    ),
                    "max_devices_ever": self._max_devices_ever,
                }
            )
        except Exception:
            _LOGGER.debug("Could not save persistent stats meta", exc_info=True)

    async def _async_update_persistent_device_meta(
        self, total_devices: int
    ) -> tuple[int, str | None, int]:
        """Update and return instance age + first seen + max devices ever."""
        now = datetime.datetime.now(datetime.timezone.utc)
        changed = False

        if self._instance_first_seen_utc is None:
            self._instance_first_seen_utc = now
            changed = True

        if total_devices > self._max_devices_ever:
            self._max_devices_ever = total_devices
            changed = True

        if changed:
            await self._async_save_meta()

        first_seen_iso = (
            self._instance_first_seen_utc.isoformat()
            if self._instance_first_seen_utc is not None
            else None
        )
        instance_age_days = (
            max(0, (now - self._instance_first_seen_utc).days)
            if self._instance_first_seen_utc is not None
            else 0
        )

        return instance_age_days, first_seen_iso, self._max_devices_ever

    # ------------------------------------------------------------------
    # Core stats
    # ------------------------------------------------------------------

    async def _collect_core_stats(self) -> dict[str, Any]:
        """Collect useful / actionable statistics."""
        hass = self.hass

        # ── Entity & device counts ──────────────────────────────────
        all_states = hass.states.async_all()
        total_entities: int = len(all_states)

        total_devices: int = 0
        try:
            from homeassistant.helpers import device_registry as dr
            dev_reg = dr.async_get(hass)
            total_devices = len(dev_reg.devices)
        except Exception:
            _LOGGER.debug("Could not access device registry", exc_info=True)

        (
            instance_age_days,
            instance_first_seen_utc,
            max_devices_ever,
        ) = await self._async_update_persistent_device_meta(total_devices)

        # ── Entity registry stats ────────────────────────────────────
        disabled_entities: int = 0
        try:
            from homeassistant.helpers import entity_registry as er
            ent_reg = er.async_get(hass)
            disabled_entities = sum(
                1 for e in ent_reg.entities.values() if e.disabled
            )
        except Exception:
            _LOGGER.debug("Could not access entity registry", exc_info=True)

        # ── Integration count ────────────────────────────────────────
        integrations_count: int = len(hass.config_entries.async_entries())

        # ── Domain-specific counts ───────────────────────────────────
        domain_counts: dict[str, int] = {}
        unavailable_count: int = 0
        unknown_count: int = 0
        for s in all_states:
            domain = s.entity_id.split(".")[0]
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
            if s.state == "unavailable":
                unavailable_count += 1
            elif s.state == "unknown":
                unknown_count += 1

        automation_count: int = domain_counts.get("automation", 0)
        script_count: int = domain_counts.get("script", 0)
        scene_count: int = domain_counts.get("scene", 0)
        light_count: int = domain_counts.get("light", 0)
        switch_count: int = domain_counts.get("switch", 0)
        binary_sensor_count: int = domain_counts.get("binary_sensor", 0)
        sensor_count: int = domain_counts.get("sensor", 0)
        person_count: int = domain_counts.get("person", 0)
        camera_count: int = domain_counts.get("camera", 0)
        media_player_count: int = domain_counts.get("media_player", 0)
        cover_count: int = domain_counts.get("cover", 0)
        climate_count: int = domain_counts.get("climate", 0)
        unique_domains_count: int = len(domain_counts)

        # ── Uptime ────────────────────────────────────────────────────
        # psutil.boot_time() returns the host OS boot timestamp.
        # We fall back to 0 if psutil is unavailable.
        uptime_days: int = 0
        uptime_hours: float = 0.0
        try:
            import homeassistant.util.dt as dt_util
            boot_time: datetime.datetime | None = None

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
                uptime_hours = round(max(0.0, delta.total_seconds() / 3600), 1)
        except Exception:
            _LOGGER.debug("Could not calculate uptime", exc_info=True)

        # ── Active entities in last 24h ───────────────────────────────
        active_entities_24h: int = 0
        try:
            import homeassistant.util.dt as dt_util
            cutoff = dt_util.utcnow() - datetime.timedelta(hours=24)
            active_entities_24h = sum(
                1
                for s in all_states
                if s.last_changed is not None and s.last_changed >= cutoff
            )
        except Exception:
            _LOGGER.debug("Could not calculate active entities", exc_info=True)

        # ── Host telemetry (CPU / RAM) ────────────────────────────────
        host_cpu_pct: float | None = None
        host_ram_pct: float | None = None
        host_disk_pct: float | None = None

        if self.enable_host_telemetry:
            try:
                import psutil  # type: ignore[import]

                # psutil calls are blocking — push to thread pool
                def _read_psutil() -> tuple[float, float, float]:
                    cpu = psutil.cpu_percent(interval=0.5)
                    ram = psutil.virtual_memory().percent
                    disk = psutil.disk_usage("/").percent
                    return cpu, ram, disk

                host_cpu_pct, host_ram_pct, host_disk_pct = (
                    await self.hass.async_add_executor_job(_read_psutil)
                )
                _LOGGER.debug(
                    "CPU: %.1f%% / RAM: %.1f%% / Disk: %.1f%%",
                    host_cpu_pct, host_ram_pct, host_disk_pct,
                )
            except ImportError:
                _LOGGER.debug(
                    "psutil not installed — host telemetry unavailable. "
                    "Install psutil or disable host telemetry in options."
                )
            except Exception:
                _LOGGER.debug("Error reading host telemetry", exc_info=True)

        # ── Energy sensors (current state sum) ────────────────────────
        # Note: we sum the *current* state values of all energy (kWh/Wh)
        # sensors as a proxy for 24h consumption. For accurate historical
        # totals, HA's Statistics subsystem would need to be queried.
        energy_24h_kwh: float = 0.0
        energy_entity_count: int = 0
        try:
            energy_24h_kwh, energy_entity_count = self._aggregate_energy(all_states)
        except Exception:
            _LOGGER.debug("Could not aggregate energy stats", exc_info=True)

        # ── Lights currently on ───────────────────────────────────────
        lights_on: int = sum(
            1 for s in all_states
            if s.entity_id.startswith("light.") and s.state == "on"
        )

        return {
            "total_entities": total_entities,
            "total_devices": total_devices,
            "instance_age_days": instance_age_days,
            "instance_first_seen_utc": instance_first_seen_utc,
            "max_devices_ever": max_devices_ever,
            "disabled_entities": disabled_entities,
            "integrations_count": integrations_count,
            "unique_domains_count": unique_domains_count,
            "domain_counts": domain_counts,
            "unavailable_count": unavailable_count,
            "unknown_count": unknown_count,
            "automation_count": automation_count,
            "script_count": script_count,
            "scene_count": scene_count,
            "light_count": light_count,
            "switch_count": switch_count,
            "binary_sensor_count": binary_sensor_count,
            "sensor_count": sensor_count,
            "person_count": person_count,
            "camera_count": camera_count,
            "media_player_count": media_player_count,
            "cover_count": cover_count,
            "climate_count": climate_count,
            "lights_on": lights_on,
            "uptime_days": uptime_days,
            "uptime_hours": uptime_hours,
            "active_entities_24h": active_entities_24h,
            "host_cpu_pct": host_cpu_pct,
            "host_ram_pct": host_ram_pct,
            "host_disk_pct": host_disk_pct,
            "energy_24h_kwh": energy_24h_kwh,
            "energy_entity_count": energy_entity_count,
        }

    # ------------------------------------------------------------------
    # Fun / useless stats
    # NOTE: This method is called via async_add_executor_job, so it runs
    # in a worker thread.  It must NOT access hass directly — all HA data
    # must be passed in as arguments captured on the event loop.
    # ------------------------------------------------------------------

    @staticmethod
    def _collect_fun_stats_sync(
        all_states: list[State],
        everything_off: bool,
    ) -> dict[str, Any]:
        """Collect purely-for-fun statistics (synchronous, runs in executor).

        Parameters
        ----------
        all_states:
            Snapshot of ``hass.states.async_all()`` taken on the event loop
            before this method was dispatched.  Safe to read from any thread.
        everything_off:
            Pre-computed flag: True when no light entity is ``on``.
        """
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

        # ── Longest / shortest entity ID ─────────────────────────────
        longest_entity_id: str = max(entity_ids, key=len) if entity_ids else ""
        shortest_entity_id: str = min(entity_ids, key=len) if entity_ids else ""

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

        # ── Most redundant name (most duplicated friendly name) ───────
        name_freq: dict[str, int] = {}
        for name in all_names:
            clean = name.strip().lower()
            if clean:
                name_freq[clean] = name_freq.get(clean, 0) + 1

        most_redundant_name: str = "N/A"
        if name_freq:
            best = max(name_freq, key=lambda n: (name_freq[n], -len(n)))
            if name_freq[best] > 1:
                most_redundant_name = f"{best!r} (×{name_freq[best]})"

        # ── Names that contain numbers ────────────────────────────────
        names_with_numbers: int = sum(
            1 for name in all_names if any(ch.isdigit() for ch in name)
        )

        # ── Daily rotating quotes / mascots ──────────────────────────
        day_of_year: int = datetime.date.today().timetuple().tm_yday
        random_daily_quote: str = DEVICE_QUOTES[day_of_year % len(DEVICE_QUOTES)]
        house_mascot: str = HOUSE_MASCOTS[day_of_year % len(HOUSE_MASCOTS)]

        return {
            "most_used_emoji": most_used_emoji,
            "avg_entity_id_length": round(avg_entity_id_length, 2),
            "longest_entity_id": longest_entity_id,
            "shortest_entity_id": shortest_entity_id,
            "devices_named_after_pokemon": pokemon_count,
            "emoji_density": emoji_density,
            "most_redundant_name": most_redundant_name,
            "names_with_numbers": names_with_numbers,
            "random_daily_quote": random_daily_quote,
            "house_mascot": house_mascot,
            # Pre-computed on the event loop and passed in
            "everything_off": everything_off,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _aggregate_energy(all_states: list[Any]) -> tuple[float, int]:
        """Sum the state values of all energy sensors (kWh).

        Returns a tuple of (total_kwh, number_of_contributing_entities).
        """
        total: float = 0.0
        count: int = 0
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
                    count += 1
                except ValueError:
                    pass
        return round(total, 3), count
