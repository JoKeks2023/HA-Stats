#!/usr/bin/with-contenv bashio

# Read add-on options
HA_URL=$(bashio::config 'ha_url')
HA_TOKEN=$(bashio::config 'ha_token')
REFRESH=$(bashio::config 'refresh_interval')

# The Supervisor injects SUPERVISOR_TOKEN automatically; use it when no manual
# token is configured.
if [ -z "${HA_TOKEN}" ]; then
    HA_TOKEN="${SUPERVISOR_TOKEN}"
fi

export HA_URL HA_TOKEN REFRESH_INTERVAL="${REFRESH}"

bashio::log.info "Starting Vibecoden HA Stats Dashboard on port 8099 ..."
exec python3 /app/app.py
