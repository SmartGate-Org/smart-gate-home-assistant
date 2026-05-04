"""Config flow for Smart Gate."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

import voluptuous as vol

from .api import SmartGateApiClient, SmartGateApiError, SmartGateRenameNotSupported
from .const import (
    CONF_DEVICE_ID,
    CONF_FRIENDLY_NAME_OVERRIDE,
    CONF_HOST,
    CONF_POLL_INTERVAL,
    CONF_PORT,
    CONF_PRODUCT,
    DEFAULT_PORT,
    DOMAIN,
    MAX_SCAN_INTERVAL_SECONDS,
    MIN_SCAN_INTERVAL_SECONDS,
    PRODUCT_DISPLAY_NAMES,
    SCAN_INTERVAL_SECONDS,
    SMART_GATE_ZEROCONF_TYPE,
    SUPPORTED_PRODUCTS,
)

_LOGGER = logging.getLogger(__name__)


async def _async_get_info(
    hass: HomeAssistant,
    host: str,
    port: int,
) -> dict[str, Any]:
    """Fetch and validate Smart Gate device information."""
    session = async_get_clientsession(hass)
    api = SmartGateApiClient(session, host, port)
    info = await api.get_info()

    product = info.get("product")
    if product not in SUPPORTED_PRODUCTS:
        raise UnsupportedProduct(product)

    return info


def _decode_zeroconf_properties(properties: dict[Any, Any]) -> dict[str, str]:
    """Decode zeroconf TXT properties into a simple string dictionary."""
    decoded: dict[str, str] = {}
    for key, value in properties.items():
        if isinstance(key, bytes):
            key = key.decode(errors="ignore")
        if isinstance(value, bytes):
            value = value.decode(errors="ignore")
        if isinstance(key, str) and isinstance(value, str):
            decoded[key.lower()] = value
    return decoded


def _zeroconf_port(properties: dict[str, str], fallback: int) -> int:
    """Return a valid port from TXT properties or the service record."""
    try:
        port = int(properties.get(CONF_PORT, fallback))
    except (TypeError, ValueError):
        return fallback
    if 1 <= port <= 65535:
        return port
    return fallback


def _device_title(info: dict[str, Any]) -> str:
    """Return a friendly config entry title."""
    friendly_name = info.get("friendly_name")
    if isinstance(friendly_name, str) and friendly_name.strip():
        return friendly_name.strip()

    hostname = info.get("hostname")
    if isinstance(hostname, str) and hostname.strip():
        return hostname.strip()

    product = info.get(CONF_PRODUCT)
    device_id = info.get(CONF_DEVICE_ID)
    display_product = PRODUCT_DISPLAY_NAMES.get(product, product)
    if isinstance(display_product, str) and isinstance(device_id, str):
        return f"{display_product} {device_id}"
    if isinstance(product, str) and isinstance(device_id, str):
        return f"{product} {device_id}"
    return "Smart Gate"


class UnsupportedProduct(Exception):
    """Raised when the discovered product is not supported."""


class SmartGateConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a Smart Gate config flow."""

    VERSION = 1
    _discovered_data: dict[str, Any] | None = None
    _discovered_placeholders: dict[str, str] | None = None
    _discovered_title: str | None = None

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return SmartGateOptionsFlow(config_entry)

    async def async_step_zeroconf(
        self,
        discovery_info: ZeroconfServiceInfo,
    ) -> FlowResult:
        """Handle zeroconf discovery."""
        if discovery_info.type != SMART_GATE_ZEROCONF_TYPE:
            return self.async_abort(reason="unsupported_product")

        properties = _decode_zeroconf_properties(discovery_info.properties or {})
        host = discovery_info.host
        port = _zeroconf_port(properties, discovery_info.port or DEFAULT_PORT)
        _LOGGER.debug(
            "Discovered Smart Gate service at %s:%s with TXT properties %s",
            host,
            port,
            properties,
        )

        try:
            info = await _async_get_info(self.hass, host, port)
        except UnsupportedProduct:
            return self.async_abort(reason="unsupported_product")
        except SmartGateApiError:
            return self.async_abort(reason="cannot_connect")

        device_id = info[CONF_DEVICE_ID]
        await self.async_set_unique_id(device_id)
        self._abort_if_unique_id_configured()

        title = _device_title(info)
        self.context["title_placeholders"] = {"name": title}
        self._discovered_data = {
            CONF_HOST: host,
            CONF_PORT: port,
            CONF_DEVICE_ID: device_id,
            CONF_PRODUCT: info[CONF_PRODUCT],
        }
        self._discovered_placeholders = {
            "device_name": title,
        }
        self._discovered_title = title
        return await self.async_step_zeroconf_confirm()

    async def async_step_zeroconf_confirm(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Confirm a discovered Smart Gate device."""
        if self._discovered_data is None or self._discovered_placeholders is None:
            return self.async_abort(reason="cannot_connect")

        if user_input is not None:
            return self.async_create_entry(
                title=self._discovered_title or "Smart Gate",
                data=self._discovered_data,
            )

        return self.async_show_form(
            step_id="zeroconf_confirm",
            description_placeholders=self._discovered_placeholders,
        )

    def _create_config_entry(self, info: dict[str, Any], host: str, port: int) -> FlowResult:
        """Create a config entry from validated device information."""
        device_id = info[CONF_DEVICE_ID]
        return self.async_create_entry(
            title=_device_title(info),
            data={
                CONF_HOST: host,
                CONF_PORT: port,
                CONF_DEVICE_ID: device_id,
                CONF_PRODUCT: info[CONF_PRODUCT],
            },
        )

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Handle manual setup."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            port = int(user_input.get(CONF_PORT, DEFAULT_PORT))

            try:
                info = await _async_get_info(self.hass, host, port)
            except UnsupportedProduct:
                errors["base"] = "unsupported_product"
            except SmartGateApiError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected Smart Gate setup error")
                errors["base"] = "unknown"
            else:
                device_id = info[CONF_DEVICE_ID]
                await self.async_set_unique_id(device_id)
                self._abort_if_unique_id_configured()

                return self._create_config_entry(info, host, port)

        return self.async_show_form(
            step_id="user",
            data_schema=self._user_schema(),
            errors=errors,
        )

    @callback
    def _user_schema(self) -> vol.Schema:
        """Return the manual setup schema."""
        return vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=1, max=65535),
                ),
            }
        )


class SmartGateOptionsFlow(config_entries.OptionsFlow):
    """Handle Smart Gate options."""

    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._entry = entry

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Manage Smart Gate options."""
        errors: dict[str, str] = {}
        runtime_data = getattr(self._entry, "runtime_data", None)
        info = runtime_data.info if runtime_data is not None else {}
        current_name = _device_title(info) if info else self._entry.title
        current_interval = int(
            self._entry.options.get(CONF_POLL_INTERVAL, SCAN_INTERVAL_SECONDS)
        )

        if user_input is not None:
            new_name = str(user_input.get(CONF_FRIENDLY_NAME_OVERRIDE, "")).strip()
            poll_interval = int(user_input.get(CONF_POLL_INTERVAL, current_interval))
            options = dict(self._entry.options)
            options[CONF_POLL_INTERVAL] = poll_interval
            name_changed = bool(new_name and new_name != current_name)

            if name_changed:
                session = async_get_clientsession(self.hass)
                api = SmartGateApiClient(
                    session,
                    self._entry.data[CONF_HOST],
                    int(self._entry.data.get(CONF_PORT, DEFAULT_PORT)),
                )
                try:
                    response = await api.set_name(new_name)
                except SmartGateRenameNotSupported:
                    errors["base"] = "rename_not_supported"
                except SmartGateApiError:
                    errors["base"] = "cannot_update_name"
                else:
                    applied_name = response.get("friendly_name", new_name)
                    options[CONF_FRIENDLY_NAME_OVERRIDE] = applied_name
                    self.hass.config_entries.async_update_entry(
                        self._entry,
                        title=applied_name,
                    )
                    return self.async_create_entry(title="", data=options)

            if not errors:
                if not new_name:
                    options.pop(CONF_FRIENDLY_NAME_OVERRIDE, None)
                self.hass.config_entries.async_update_entry(
                    self._entry,
                    title=new_name or current_name,
                )
                return self.async_create_entry(title="", data=options)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_FRIENDLY_NAME_OVERRIDE,
                        default=current_name,
                    ): str,
                    vol.Optional(
                        CONF_POLL_INTERVAL,
                        default=current_interval,
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(
                            min=MIN_SCAN_INTERVAL_SECONDS,
                            max=MAX_SCAN_INTERVAL_SECONDS,
                        ),
                    ),
                }
            ),
            errors=errors,
        )
