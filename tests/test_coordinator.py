"""Unit tests for VibeStatsCoordinator pure-logic helpers.

These tests exercise the static / synchronous helpers without requiring
a real Home Assistant instance.  We test only the two static methods:

  * VibeStatsCoordinator._aggregate_energy
  * VibeStatsCoordinator._collect_fun_stats_sync

Both methods receive plain Python objects (no HA internals) so we can
test them by directly copying/extracting their logic here.
"""
from __future__ import annotations

import datetime
import re
from types import SimpleNamespace
from typing import Any

import pytest

# ---------------------------------------------------------------------------
# Re-implement the two static helpers inline so we have zero HA dependencies
# ---------------------------------------------------------------------------

POKEMON_NAMES = ["pikachu", "eevee", "mewtwo", "bulbasaur", "charmander"]
DEVICE_QUOTES = ["Quote A", "Quote B", "Quote C"]
HOUSE_MASCOTS = ["🦙 Llama", "🐉 Dragon", "🦊 Fox"]

_EMOJI_RE = re.compile(
    "[\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F900-\U0001F9FF"
    "\u2600-\u26FF"
    "\u2700-\u27BF"
    "]+",
    flags=re.UNICODE,
)


def _make_state(
    entity_id: str,
    state: str = "on",
    attributes: dict[str, Any] | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        entity_id=entity_id,
        state=state,
        attributes=attributes or {},
        last_changed=datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc),
    )


def _aggregate_energy(all_states):
    """Direct copy of VibeStatsCoordinator._aggregate_energy."""
    total: float = 0.0
    count: int = 0
    for state in all_states:
        unit = state.attributes.get("unit_of_measurement", "")
        if unit.lower() in ("kwh", "wh") and state.state not in (
            "unavailable", "unknown", "", None,
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


def _collect_fun_stats_sync(all_states, everything_off: bool):
    """Direct copy of VibeStatsCoordinator._collect_fun_stats_sync."""
    entity_ids = [s.entity_id for s in all_states]
    all_names = []
    for s in all_states:
        name = s.attributes.get("friendly_name") or ""
        if name:
            all_names.append(name)

    avg_entity_id_length = (
        sum(len(eid) for eid in entity_ids) / len(entity_ids) if entity_ids else 0.0
    )
    longest_entity_id = max(entity_ids, key=len) if entity_ids else ""
    shortest_entity_id = min(entity_ids, key=len) if entity_ids else ""

    emoji_counts: dict[str, int] = {}
    total_chars = 0
    emoji_chars = 0
    for name in all_names:
        total_chars += len(name)
        for match in _EMOJI_RE.finditer(name):
            emoji_chars += len(match.group())
            for ch in match.group():
                emoji_counts[ch] = emoji_counts.get(ch, 0) + 1

    most_used_emoji = (
        max(emoji_counts, key=lambda e: emoji_counts[e]) if emoji_counts else "🤷"
    )
    emoji_density = round(emoji_chars / total_chars * 100, 2) if total_chars > 0 else 0.0

    pokemon_count = sum(
        1 for name in all_names if any(p in name.lower() for p in POKEMON_NAMES)
    )

    name_freq: dict[str, int] = {}
    for name in all_names:
        clean = name.strip().lower()
        if clean:
            name_freq[clean] = name_freq.get(clean, 0) + 1

    most_redundant_name = "N/A"
    if name_freq:
        best = max(name_freq, key=lambda n: (name_freq[n], -len(n)))
        if name_freq[best] > 1:
            most_redundant_name = f"{best!r} (×{name_freq[best]})"

    names_with_numbers = sum(1 for name in all_names if any(ch.isdigit() for ch in name))

    day_of_year = datetime.date.today().timetuple().tm_yday
    random_daily_quote = DEVICE_QUOTES[day_of_year % len(DEVICE_QUOTES)]
    house_mascot = HOUSE_MASCOTS[day_of_year % len(HOUSE_MASCOTS)]

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
        "everything_off": everything_off,
    }


# ---------------------------------------------------------------------------
# Tests for _aggregate_energy
# ---------------------------------------------------------------------------

class TestAggregateEnergy:
    def test_empty(self):
        total, count = _aggregate_energy([])
        assert total == 0.0
        assert count == 0

    def test_kwh_sensors(self):
        states = [
            _make_state("sensor.a", "10.5", {"unit_of_measurement": "kWh"}),
            _make_state("sensor.b", "4.5", {"unit_of_measurement": "kWh"}),
        ]
        total, count = _aggregate_energy(states)
        assert total == 15.0
        assert count == 2

    def test_wh_conversion(self):
        states = [_make_state("sensor.a", "1000", {"unit_of_measurement": "Wh"})]
        total, count = _aggregate_energy(states)
        assert total == 1.0
        assert count == 1

    def test_unavailable_skipped(self):
        states = [
            _make_state("sensor.a", "unavailable", {"unit_of_measurement": "kWh"}),
            _make_state("sensor.b", "unknown", {"unit_of_measurement": "kWh"}),
            _make_state("sensor.c", "5.0", {"unit_of_measurement": "kWh"}),
        ]
        total, count = _aggregate_energy(states)
        assert total == 5.0
        assert count == 1

    def test_mixed_units_ignored(self):
        states = [
            _make_state("sensor.a", "100", {"unit_of_measurement": "°C"}),
            _make_state("sensor.b", "2.0", {"unit_of_measurement": "kWh"}),
        ]
        total, count = _aggregate_energy(states)
        assert total == 2.0
        assert count == 1

    def test_invalid_state_skipped(self):
        states = [_make_state("sensor.a", "not_a_number", {"unit_of_measurement": "kWh"})]
        total, count = _aggregate_energy(states)
        assert total == 0.0
        assert count == 0

    def test_case_insensitive_unit(self):
        states = [_make_state("sensor.a", "3.0", {"unit_of_measurement": "KWH"})]
        total, count = _aggregate_energy(states)
        assert total == 3.0
        assert count == 1


# ---------------------------------------------------------------------------
# Tests for _collect_fun_stats_sync
# ---------------------------------------------------------------------------

class TestCollectFunStats:
    def test_empty_states(self):
        result = _collect_fun_stats_sync([], everything_off=True)
        assert result["avg_entity_id_length"] == 0.0
        assert result["devices_named_after_pokemon"] == 0
        assert result["most_used_emoji"] == "🤷"
        assert result["emoji_density"] == 0.0
        assert result["most_redundant_name"] == "N/A"
        assert result["everything_off"] is True
        assert result["names_with_numbers"] == 0
        assert result["longest_entity_id"] == ""
        assert result["shortest_entity_id"] == ""

    def test_pokemon_detection(self):
        states = [
            _make_state("sensor.pikachu_temp", attributes={"friendly_name": "Pikachu Temp"}),
            _make_state("sensor.normal", attributes={"friendly_name": "Living Room"}),
        ]
        result = _collect_fun_stats_sync(states, everything_off=True)
        assert result["devices_named_after_pokemon"] == 1

    def test_pokemon_case_insensitive(self):
        states = [
            _make_state("sensor.a", attributes={"friendly_name": "EEVEE sensor"}),
        ]
        result = _collect_fun_stats_sync(states, everything_off=True)
        assert result["devices_named_after_pokemon"] == 1

    def test_avg_entity_id_length(self):
        states = [_make_state("a.bc"), _make_state("a.bcde")]  # lengths 4, 6
        result = _collect_fun_stats_sync(states, everything_off=True)
        assert result["avg_entity_id_length"] == 5.0

    def test_emoji_detection(self):
        states = [_make_state("sensor.a", attributes={"friendly_name": "💡 Light"})]
        result = _collect_fun_stats_sync(states, everything_off=True)
        assert result["most_used_emoji"] == "💡"
        assert result["emoji_density"] > 0

    def test_redundant_name(self):
        states = [
            _make_state("sensor.a", attributes={"friendly_name": "Bedroom"}),
            _make_state("sensor.b", attributes={"friendly_name": "Bedroom"}),
            _make_state("sensor.c", attributes={"friendly_name": "Bedroom"}),
        ]
        result = _collect_fun_stats_sync(states, everything_off=True)
        assert "'bedroom'" in result["most_redundant_name"]
        assert "×3" in result["most_redundant_name"]

    def test_no_redundancy_when_all_unique(self):
        states = [
            _make_state("sensor.a", attributes={"friendly_name": "Kitchen"}),
            _make_state("sensor.b", attributes={"friendly_name": "Bathroom"}),
        ]
        result = _collect_fun_stats_sync(states, everything_off=True)
        assert result["most_redundant_name"] == "N/A"

    def test_names_with_numbers(self):
        states = [
            _make_state("sensor.a", attributes={"friendly_name": "Room 1"}),
            _make_state("sensor.b", attributes={"friendly_name": "Room 2"}),
            _make_state("sensor.c", attributes={"friendly_name": "Living Room"}),
        ]
        result = _collect_fun_stats_sync(states, everything_off=True)
        assert result["names_with_numbers"] == 2

    def test_everything_off_passed_through(self):
        assert _collect_fun_stats_sync([], everything_off=True)["everything_off"] is True
        assert _collect_fun_stats_sync([], everything_off=False)["everything_off"] is False

    def test_longest_shortest_entity_id(self):
        states = [
            _make_state("a.b"),
            _make_state("sensor.very_long_entity_id_name"),
        ]
        result = _collect_fun_stats_sync(states, everything_off=True)
        assert result["longest_entity_id"] == "sensor.very_long_entity_id_name"
        assert result["shortest_entity_id"] == "a.b"

    def test_daily_quote_and_mascot_valid(self):
        result = _collect_fun_stats_sync([], everything_off=True)
        assert isinstance(result["random_daily_quote"], str)
        assert len(result["random_daily_quote"]) > 0
        assert isinstance(result["house_mascot"], str)
        assert len(result["house_mascot"]) > 0

    def test_no_friendly_name_still_counts_entity_id(self):
        """Entities without friendly_name should still count toward avg_entity_id_length."""
        states = [_make_state("sensor.no_name")]
        result = _collect_fun_stats_sync(states, everything_off=True)
        assert result["avg_entity_id_length"] == len("sensor.no_name")
        # But no name stats
        assert result["most_used_emoji"] == "🤷"

