"""Constants for the Smart Gate integration."""

DOMAIN = "smart_gate"
MANUFACTURER = "Smart Gate"

CONF_HOST = "host"
CONF_PORT = "port"
CONF_TOKEN = "token"
CONF_AUTH_MODE = "auth_mode"
CONF_DEVICE_ID = "device_id"
CONF_PRODUCT = "product"
CONF_FRIENDLY_NAME_OVERRIDE = "friendly_name_override"
CONF_POLL_INTERVAL = "poll_interval"

DEFAULT_PORT = 8080
SCAN_INTERVAL_SECONDS = 5
MIN_SCAN_INTERVAL_SECONDS = 3
MAX_SCAN_INTERVAL_SECONDS = 60
INFO_REFRESH_INTERVAL_UPDATES = 12

AUTH_MODE_MANUAL = "manual"
AUTH_MODE_OPTIONAL = "optional"
AUTH_MODE_REQUIRED = "required"

SMART_GATE_ZEROCONF_TYPE = "_smartgate._tcp.local."

SUPPORTED_PRODUCTS = {
    "SG-Load-Box",
}

PRODUCT_DISPLAY_NAMES = {
    "SG-Load-Box": "Smart Gate Load Box",
}
