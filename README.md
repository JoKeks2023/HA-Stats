# 🏠 HA Stats

> **A Home Assistant custom integration that turns your smart home into a stats-nerd playground.**
> Useful metrics side-by-side with hilariously useless ones — because why not?

---

## ✨ Features

| Category | What you get |
|---|---|
| **Core stats** | Device count, entity count, integrations, automations, uptime, CPU & RAM, energy |
| **Fun stats** | Most-used emoji, Pokémon-named devices, daily mascot, party-mode detector and more |
| **Options flow** | Tweak poll interval, toggle fun stats & host telemetry — all from the UI |
| **No dependencies** | Pure Home Assistant Core (psutil optional for CPU/RAM) |

---

## 📦 Installation

### Option A — Manual (HACS-style)

1. Copy the `custom_components/vibecoden_ha_stats` folder into your HA
   `config/custom_components/` directory:

   ```
   config/
   └── custom_components/
       └── vibecoden_ha_stats/
           ├── __init__.py
           ├── binary_sensor.py
           ├── config_flow.py
           ├── const.py
           ├── coordinator.py
           ├── manifest.json
           ├── sensor.py
           ├── strings.json
           └── translations/
               └── en.json
   ```

2. **Restart** Home Assistant.

3. Go to **Settings → Devices & Services → Add Integration** and search for
   **"Vibecoden HA Stats"**.

4. Click **Submit** — no credentials required.

### Option B — HACS (future)

Once listed in HACS, install via **HACS → Integrations → Vibecoden HA Stats**.

---

## ⚙️ Options

After installation, click **Configure** on the integration card to adjust:

| Option | Default | Description |
|---|---|---|
| `scan_interval` | `300` s | How often stats are refreshed (30 – 86 400 s) |
| `enable_fun_stats` | `true` | Toggle all fun / useless sensors |
| `enable_host_telemetry` | `true` | Enable CPU, RAM & Disk sensors (needs `psutil`) |

> **psutil** ships with Home Assistant OS / Supervised. On Container installs
> you may need `pip install psutil` inside the HA container if CPU/RAM/Disk sensors
> show `unknown`.

---

## 📊 Available Entities

### Core sensors (always on)

| Entity ID | Unit | Description |
|---|---|---|
| `sensor.total_devices` | — | Total devices in device registry |
| `sensor.max_devices_ever` | — | Highest number of devices ever seen since stats tracking started |
| `sensor.instance_age_days` | days | Age of the HA instance in days since stats tracking started |
| `sensor.total_entities` | — | Total entity states (with domain breakdown attribute) |
| `sensor.integrations_count` | — | Number of configured integrations |
| `sensor.unique_domains_count` | — | Number of unique entity domains |
| `sensor.automation_count` | — | Number of automation entities |
| `sensor.script_count` | — | Number of script entities |
| `sensor.scene_count` | — | Number of scene entities |
| `sensor.light_count` | — | Number of light entities |
| `sensor.switch_count` | — | Number of switch entities |
| `sensor.binary_sensor_count` | — | Number of binary sensor entities |
| `sensor.sensor_count` | — | Number of sensor entities |
| `sensor.person_count` | — | Number of person entities |
| `sensor.camera_count` | — | Number of camera entities |
| `sensor.media_player_count` | — | Number of media player entities |
| `sensor.cover_count` | — | Number of cover/blind entities |
| `sensor.climate_count` | — | Number of climate/thermostat entities |
| `sensor.unavailable_count` | — | Entities currently in `unavailable` state |
| `sensor.unknown_count` | — | Entities currently in `unknown` state |
| `sensor.disabled_entities` | — | Disabled entities in entity registry |
| `sensor.lights_on` | — | Lights currently switched on |
| `sensor.uptime_days` | days | Host uptime in days (psutil) |
| `sensor.uptime_hours` | h | Host uptime in hours (psutil) |
| `sensor.active_devices_24h` | — | Entities that changed state in last 24 h |
| `sensor.host_cpu_pct` | % | Host CPU usage (psutil) |
| `sensor.host_ram_pct` | % | Host RAM usage (psutil) |
| `sensor.host_disk_pct` | % | Host disk (/) usage (psutil) |
| `sensor.energy_24h_kwh` | kWh | Sum of all energy sensor states |

### Fun sensors *(toggleable via Options)*

| Entity ID | Description |
|---|---|
| `sensor.most_used_emoji` | Most frequent emoji across friendly names |
| `sensor.avg_entity_id_length` | Average character length of entity IDs (+ longest/shortest as attributes) |
| `sensor.devices_named_after_pokemon` | Devices whose names contain a Pokémon name |
| `sensor.emoji_density` | % of friendly-name characters that are emojis |
| `sensor.most_redundant_name` | Most duplicated friendly name |
| `sensor.names_with_numbers` | Count of entity names that contain a digit |
| `sensor.random_daily_device_quote` | Rotates daily — motivational device wisdom |
| `sensor.house_mascot` | Your home's daily spirit animal 🦙 |
| `binary_sensor.everything_off_party_mode` | `on` when zero lights are on |

---

## 🖥️ Add-on Dashboard (Full Custom App)

A standalone web dashboard is provided as a Home Assistant add-on in the
`ha_addon/` directory. It fetches live data from the HA REST API and renders
every stat in a beautiful dark-mode card UI with:

- **Colour-coded alerts** — Unavailable / Unknown entities turn red automatically
- **Gauge bars** — CPU, RAM and Disk show a live bar (green → yellow → red)
- **Auto-refresh** — configurable polling interval (default 30 s)
- **Daily quote** — scrolls across the bottom with the house mascot

### Installation

1. In Home Assistant go to **Settings → Add-ons → Add-on Store → ⋮ → Repositories**.
2. Add `https://github.com/JoKeks2023/HA-Stats` and install
   **Vibecoden HA Stats Dashboard**.
3. Click **Start** — the dashboard appears as a sidebar panel called **HA Stats**.

### Manual install (for development)

```bash
# Copy the add-on folder to your HA add-ons directory
cp -r ha_addon/ /path/to/homeassistant/addons/vibecoden_ha_stats_dashboard/

# Rebuild and start from the add-on store UI
```

### Add-on structure

```
ha_addon/
├── config.yaml          # Add-on metadata, ports, options schema
├── Dockerfile           # Python + Flask image
├── run.sh               # Startup script (reads Supervisor config)
└── app/
    ├── app.py           # Flask app — serves / and /api/stats
    └── templates/
        └── index.html   # Single-page dashboard (vanilla JS)
```

---

## 📋 Lovelace Dashboard YAML

A ready-to-use Lovelace dashboard is provided at
[`lovelace/ha_stats_dashboard.yaml`](lovelace/ha_stats_dashboard.yaml).
It contains four views:

| View | Contents |
|---|---|
| **Overview** | Markdown summary + core & health glance cards + device-history graph |
| **System** | CPU / RAM / Disk gauges + uptime + history graphs |
| **Entities** | Full entity-count breakdown by domain |
| **Fun Stats** | All fun sensors in a 2-column grid + daily quote |

### How to use

1. Go to **Settings → Dashboards → Add Dashboard**.
2. Enable **Show in sidebar**, choose a title (e.g. *HA Stats*).
3. Click the pencil ✏️ icon → **Raw configuration editor**.
4. Paste the contents of `lovelace/ha_stats_dashboard.yaml` (starting from `views:`).

---

## 🎨 Lovelace / Dashboard Examples

### 1 — Stats Overview Card

```yaml
type: entities
title: 🏠 HA Stats Overview
entities:
  - entity: sensor.total_devices
    name: Total Devices
    icon: mdi:devices
  - entity: sensor.total_entities
    name: Total Entities
    icon: mdi:format-list-bulleted
  - entity: sensor.integrations_count
    name: Integrations
    icon: mdi:puzzle
  - entity: sensor.unique_domains_count
    name: Unique Domains
    icon: mdi:tag-multiple
  - entity: sensor.automation_count
    name: Automations
    icon: mdi:robot
  - entity: sensor.unavailable_count
    name: Unavailable
    icon: mdi:alert-circle-outline
  - entity: sensor.lights_on
    name: Lights On
    icon: mdi:lightbulb-on
  - entity: sensor.uptime_hours
    name: Uptime (h)
    icon: mdi:clock-outline
  - entity: sensor.host_cpu_pct
    name: CPU
    icon: mdi:cpu-64-bit
  - entity: sensor.host_ram_pct
    name: RAM
    icon: mdi:memory
  - entity: sensor.host_disk_pct
    name: Disk
    icon: mdi:harddisk
```

### 2 — Fun Stats / Achievement Wall

```yaml
type: grid
columns: 2
cards:
  - type: entity
    entity: sensor.most_used_emoji
    name: Most Used Emoji
    icon: mdi:emoticon-outline
  - type: entity
    entity: sensor.devices_named_after_pokemon
    name: Pokémon Devices
    icon: mdi:pokeball
  - type: entity
    entity: sensor.emoji_density
    name: Emoji Density
    icon: mdi:percent
  - type: entity
    entity: sensor.house_mascot
    name: Today's Mascot
    icon: mdi:home-heart
  - type: entity
    entity: sensor.most_redundant_name
    name: Most Redundant Name
    icon: mdi:content-duplicate
  - type: entity
    entity: sensor.names_with_numbers
    name: Names with Numbers
    icon: mdi:numeric
  - type: entity
    entity: binary_sensor.everything_off_party_mode
    name: Party Mode 🎉
    icon: mdi:party-popper
```

### 3 — Animated Markdown Counter

```yaml
type: markdown
content: |
  ## 🏠 Home at a Glance

  | | |
  |---|---|
  | 📦 Devices | **{{ states('sensor.total_devices') }}** |
  | 🔌 Entities | **{{ states('sensor.total_entities') }}** |
  | 🧩 Integrations | **{{ states('sensor.integrations_count') }}** |
  | 💡 Lights On | **{{ states('sensor.lights_on') }}** |
  | ⚠️ Unavailable | **{{ states('sensor.unavailable_count') }}** |
  | ⚡ Energy Total | **{{ states('sensor.energy_24h_kwh') }} kWh** |
  | 🖥️ CPU / RAM | **{{ states('sensor.host_cpu_pct') }}% / {{ states('sensor.host_ram_pct') }}%** |
  | 🦙 Mascot | {{ states('sensor.house_mascot') }} |
  | 💬 Quote | *{{ states('sensor.random_daily_device_quote') }}* |
```

---

## 🏗️ Architecture

```
vibecoden_ha_stats/
├── __init__.py          # async_setup_entry / async_unload_entry
├── config_flow.py       # ConfigFlow + OptionsFlow
├── const.py             # DOMAIN, PLATFORMS, defaults, lists
├── coordinator.py       # VibeStatsCoordinator (DataUpdateCoordinator)
├── sensor.py            # SensorEntity subclasses (core + fun)
├── binary_sensor.py     # BinarySensorEntity subclasses
├── manifest.json
├── strings.json
└── translations/
    └── en.json
```

**Data flow:**
1. `VibeStatsCoordinator._async_update_data()` runs every N seconds.
2. Core stats are collected async on the event loop.
3. Fun stats (string parsing) run in a thread via `run_in_executor`.
4. All entities inherit from `CoordinatorEntity` and get data via `coordinator.data`.

---

## 🔒 Privacy & Performance

- No usernames, passwords, or IP addresses are collected or stored.
- Fun stats only count/analyze entity IDs and friendly names — no state values.
- Heavy string operations run off the main loop in a thread pool executor.
- Sensitive host telemetry (CPU/RAM) can be disabled in Options.

---

## 🤝 Contributing

1. Fork the repo.
2. Create your feature branch: `git checkout -b feat/my-cool-stat`
3. Commit your changes and open a PR.

---

## 📜 License

MIT — do whatever you want, just don't blame us when your home assistant
develops an existential crisis after seeing the `vibe_everything_off_party_mode` sensor.
