"""Vibecoden HA Stats Dashboard — Flask web application.

Runs inside the Home Assistant add-on container and serves a single-page
dashboard that fetches live state from the Home Assistant REST API.
"""
from __future__ import annotations

import os
from typing import Any

import requests
from flask import Flask, jsonify, render_template

app = Flask(__name__)

# ── Configuration (injected by run.sh / Supervisor) ──────────────────────────
HA_URL: str = os.environ.get("HA_URL", "http://supervisor/core").rstrip("/")
HA_TOKEN: str = os.environ.get("HA_TOKEN", "")
REFRESH_INTERVAL: int = int(os.environ.get("REFRESH_INTERVAL", "30"))

# ── Entities shown on the dashboard ──────────────────────────────────────────
# Each entry: (entity_id, friendly_label, icon_class, section)
ENTITIES: list[tuple[str, str, str, str]] = [
    # Core — overview
    ("sensor.total_devices",        "Total Devices",         "mdi:devices",                  "core"),
    ("sensor.total_entities",       "Total Entities",        "mdi:format-list-bulleted",      "core"),
    ("sensor.integrations_count",   "Integrations",          "mdi:puzzle",                    "core"),
    ("sensor.unique_domains_count", "Unique Domains",        "mdi:tag-multiple",              "core"),
    ("sensor.automation_count",     "Automations",           "mdi:robot",                     "core"),
    ("sensor.script_count",         "Scripts",               "mdi:script-text",               "core"),
    ("sensor.scene_count",          "Scenes",                "mdi:palette",                   "core"),
    ("sensor.active_devices_24h",   "Active (24 h)",         "mdi:pulse",                     "core"),
    # Core — health
    ("sensor.lights_on",            "Lights On",             "mdi:lightbulb-on",              "health"),
    ("sensor.unavailable_count",    "Unavailable",           "mdi:alert-circle-outline",      "health"),
    ("sensor.unknown_count",        "Unknown State",         "mdi:help-circle-outline",       "health"),
    ("sensor.disabled_entities",    "Disabled Entities",     "mdi:eye-off-outline",           "health"),
    # Core — system
    ("sensor.host_cpu_pct",         "CPU %",                 "mdi:cpu-64-bit",                "system"),
    ("sensor.host_ram_pct",         "RAM %",                 "mdi:memory",                    "system"),
    ("sensor.host_disk_pct",        "Disk %",                "mdi:harddisk",                  "system"),
    ("sensor.uptime_hours",         "Uptime (h)",            "mdi:clock-outline",             "system"),
    ("sensor.uptime_days",          "Uptime (days)",         "mdi:timer-outline",             "system"),
    ("sensor.energy_24h_kwh",       "Energy 24 h (kWh)",     "mdi:lightning-bolt",            "system"),
    # Fun
    ("sensor.most_used_emoji",              "Most Used Emoji",       "mdi:emoticon-outline",   "fun"),
    ("sensor.devices_named_after_pokemon",  "Pokémon Devices",       "mdi:pokeball",           "fun"),
    ("sensor.emoji_density",                "Emoji Density %",       "mdi:percent",            "fun"),
    ("sensor.avg_entity_id_length",         "Avg Entity ID Len",     "mdi:ruler",              "fun"),
    ("sensor.most_redundant_name",          "Most Redundant Name",   "mdi:content-duplicate",  "fun"),
    ("sensor.names_with_numbers",           "Names w/ Numbers",      "mdi:numeric",            "fun"),
    ("sensor.house_mascot",                 "Today's Mascot",        "mdi:home-heart",         "fun"),
    ("sensor.random_daily_device_quote",    "Daily Quote",           "mdi:comment-quote",      "fun"),
    ("binary_sensor.everything_off_party_mode", "Party Mode 🎉",     "mdi:party-popper",       "fun"),
]


def _ha_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {HA_TOKEN}",
        "Content-Type": "application/json",
    }


def _fetch_states() -> dict[str, Any]:
    """Fetch all entity states from HA REST API and return as dict keyed by entity_id."""
    try:
        resp = requests.get(
            f"{HA_URL}/api/states",
            headers=_ha_headers(),
            timeout=10,
        )
        resp.raise_for_status()
        states: list[dict[str, Any]] = resp.json()
        return {s["entity_id"]: s for s in states}
    except Exception as exc:  # noqa: BLE001
        app.logger.error("Failed to fetch HA states: %s", exc)
        return {}


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Render the dashboard HTML."""
    return render_template(
        "index.html",
        refresh_interval=REFRESH_INTERVAL,
        entities=ENTITIES,
    )


@app.route("/api/stats")
def api_stats():
    """Return a JSON snapshot of all dashboard entity states."""
    all_states = _fetch_states()
    result: dict[str, Any] = {}
    for entity_id, label, icon, section in ENTITIES:
        state_obj = all_states.get(entity_id, {})
        result[entity_id] = {
            "label": label,
            "icon": icon,
            "section": section,
            "state": state_obj.get("state", "unavailable"),
            "attributes": state_obj.get("attributes", {}),
        }
    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8099, debug=False)
