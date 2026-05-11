"""Config flow for Smart Gate."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Awaitable, Callable, TypeVar

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import TextSelector, TextSelectorConfig, TextSelectorType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

import voluptuous as vol

from .api import (
    SmartGateApiClient,
    SmartGateApiError,
    SmartGateAuthError,
    SmartGateRenameNotSupported,
)
from .const import (
    AUTH_MODE_MANUAL,
    AUTH_MODE_OPTIONAL,
    AUTH_MODE_REQUIRED,
    CACHED_INFO_KEYS,
    CONF_AUTH_MODE,
    CONF_CACHED_INFO,
    CONF_DEVICE_ID,
    CONF_FRIENDLY_NAME_OVERRIDE,
    CONF_HOST,
    CONF_POLL_INTERVAL,
    CONF_PORT,
    CONF_PRODUCT,
    CONF_TOKEN,
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
TOKEN_SELECTOR = TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD))
SETUP_RETRY_SECONDS = 12
SETUP_RETRY_DELAY_SECONDS = 1
_T = TypeVar("_T")


class UnsupportedProduct(Exception):
    """Raised when the discovered product is not supported."""


async def _async_retry_setup_call(
    description: str,
    host: str,
    port: int,
    operation: Callable[[], Awaitable[_T]],
) -> _T:
    """Retry a setup-time local API call through transient boot outages."""
    deadline = time.monotonic() + SETUP_RETRY_SECONDS
    attempt = 1

    while True:
        try:
            return await operation()
        except SmartGateAuthError:
            raise
        except SmartGateApiError as err:
            if time.monotonic() >= deadline:
                raise
            _LOGGER.debug(
                "Smart Gate setup retry %s for %s at %s:%s after %s: %s",
                attempt,
                description,
                host,
                port,
                err.__class__.__name__,
                err,
            )
            attempt += 1
            await asyncio.sleep(SETUP_RETRY_DELAY_SECONDS)


def _token_from_input(user_input: dict[str, Any]) -> str:
    """Return the token exactly as entered, without logging it."""
    token = user_input.get(CONF_TOKEN)
    return token if isinstance(token, str) else ""


def _stored_token(data: dict[str, Any]) -> str:
    """Return a stored token without exposing it in forms by default."""
    token = data.get(CONF_TOKEN)
    return token if isinstance(token, str) else ""


async def _async_validate_device(
    hass: HomeAssistant,
    host: str,
    port: int,
    token: str | None,
) -> dict[str, Any]:
    """Fetch info and validate protected state access."""
    session = async_get_clientsession(hass)
    api = SmartGateApiClient(session, host, port, token or None)
    info = await api.get_info()

    product = info.get("product")
    if product not in SUPPORTED_PRODUCTS:
        raise UnsupportedProduct(product)

    await api.get_state()
    return info


async def _async_get_info(
    hass: HomeAssistant,
    host: str,
    port: int,
) -> dict[str, Any]:
    """Fetch public Smart Gate device information."""
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


def _zeroconf_auth_mode(properties: dict[str, str]) -> str:
    """Return the firmware-advertised local auth mode."""
    auth = properties.get(CONF_AUTH_MODE, AUTH_MODE_OPTIONAL).lower()
    if auth == AUTH_MODE_REQUIRED:
        return AUTH_MODE_REQUIRED
    return AUTH_MODE_OPTIONAL


def _device_title(info: dict[str, Any]) -> str:
    """Return a friendly config entry title."""
    friendly_name = info.get("friendly_name")
    if isinstance(friendly_name, str) and friendly_name.strip():
        return friendly_name.strip()

    product = info.get(CONF_PRODUCT)
    display_product = PRODUCT_DISPLAY_NAMES.get(product, product)
    short_id = info.get("short_id")
    if isinstance(display_product, str) and isinstance(short_id, str) and short_id:
        return f"{display_product} {short_id}"

    hostname = info.get("hostname")
    if isinstance(hostname, str) and hostname.strip():
        return hostname.strip()

    device_id = info.get(CONF_DEVICE_ID)
    if isinstance(display_product, str) and isinstance(device_id, str):
        return f"{display_product} {device_id}"
    if isinstance(product, str) and isinstance(device_id, str):
        return f"{product} {device_id}"
    return "Smart Gate"


def _cacheable_info(info: dict[str, Any]) -> dict[str, Any]:
    """Return the safe subset of /v1/info stored in the config entry."""
    return {
        key: info[key]
        for key in CACHED_INFO_KEYS
        if key in info and info[key] is not None
    }


class SmartGateConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a Smart Gate config flow."""

    VERSION = 1
    _discovered_data: dict[str, Any] | None = None
    _discovered_placeholders: dict[str, str] | None = None
    _discovered_title: str | None = None
    _reauth_entry: config_entries.ConfigEntry | None = None

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
        auth_mode = _zeroconf_auth_mode(properties)
        _LOGGER.debug("Discovered Smart Gate service at %s:%s auth=%s", host, port, auth_mode)

        try:
            info = await _async_retry_setup_call(
                "zeroconf info",
                host,
                port,
                lambda: _async_get_info(self.hass, host, port),
            )
        except UnsupportedProduct:
            return self.async_abort(reason="unsupported_product")
        except SmartGateApiError:
            return self.async_abort(reason="cannot_connect")

        device_id = info[CONF_DEVICE_ID]
        await self.async_set_unique_id(device_id)
        existing_entry = self._entry_for_unique_id(device_id)
        if existing_entry is not None:
            self._async_update_existing_entry_from_discovery(
                existing_entry,
                host,
                port,
                auth_mode,
                info,
            )
            return self.async_abort(reason="already_configured")

        title = _device_title(info)
        self.context["title_placeholders"] = {"name": title}
        self._discovered_data = {
            CONF_HOST: host,
            CONF_PORT: port,
            CONF_DEVICE_ID: device_id,
            CONF_PRODUCT: info[CONF_PRODUCT],
            CONF_AUTH_MODE: auth_mode,
            CONF_CACHED_INFO: _cacheable_info(info),
        }
        self._discovered_placeholders = {"device_name": title}
        self._discovered_title = title
        return await self.async_step_zeroconf_confirm()

    async def async_step_zeroconf_confirm(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Confirm a discovered Smart Gate device and collect token if needed."""
        if self._discovered_data is None or self._discovered_placeholders is None:
            return self.async_abort(reason="cannot_connect")

        errors: dict[str, str] = {}
        if user_input is not None:
            token = _token_from_input(user_input)
            try:
                host = self._discovered_data[CONF_HOST]
                port = int(self._discovered_data[CONF_PORT])
                info = await _async_retry_setup_call(
                    "zeroconf confirmation",
                    host,
                    port,
                    lambda: _async_validate_device(
                        self.hass,
                        host,
                        port,
                        token or None,
                    ),
                )
            except UnsupportedProduct:
                errors["base"] = "unsupported_product"
            except SmartGateAuthError:
                errors["base"] = "invalid_auth"
            except SmartGateApiError:
                errors["base"] = "cannot_connect"
            else:
                data = dict(self._discovered_data)
                data[CONF_DEVICE_ID] = info[CONF_DEVICE_ID]
                data[CONF_PRODUCT] = info[CONF_PRODUCT]
                data[CONF_CACHED_INFO] = _cacheable_info(info)
                if token:
                    data[CONF_TOKEN] = token
                return self.async_create_entry(
                    title=self._discovered_title or _device_title(info),
                    data=data,
                )

        return self.async_show_form(
            step_id="zeroconf_confirm",
            data_schema=self._token_schema(required=False),
            description_placeholders=self._discovered_placeholders,
            errors=errors,
        )

    def _create_config_entry(
        self,
        info: dict[str, Any],
        host: str,
        port: int,
        token: str,
        auth_mode: str,
    ) -> FlowResult:
        """Create a config entry from validated device information."""
        data: dict[str, Any] = {
            CONF_HOST: host,
            CONF_PORT: port,
            CONF_DEVICE_ID: info[CONF_DEVICE_ID],
            CONF_PRODUCT: info[CONF_PRODUCT],
            CONF_AUTH_MODE: auth_mode,
            CONF_CACHED_INFO: _cacheable_info(info),
        }
        if token:
            data[CONF_TOKEN] = token
        return self.async_create_entry(title=_device_title(info), data=data)

    def _entry_for_unique_id(
        self,
        unique_id: str,
    ) -> config_entries.ConfigEntry | None:
        """Return an existing entry for a discovered device ID."""
        return next(
            (
                entry
                for entry in self._async_current_entries()
                if entry.unique_id == unique_id
            ),
            None,
        )

    def _async_update_existing_entry_from_discovery(
        self,
        entry: config_entries.ConfigEntry,
        host: str,
        port: int,
        auth_mode: str,
        info: dict[str, Any],
    ) -> None:
        """Update an existing entry with discovery metadata."""
        data = dict(entry.data)
        reload_needed = False

        if data.get(CONF_HOST) != host:
            data[CONF_HOST] = host
            reload_needed = True
        if int(data.get(CONF_PORT, DEFAULT_PORT)) != port:
            data[CONF_PORT] = port
            reload_needed = True
        if data.get(CONF_AUTH_MODE) != auth_mode:
            data[CONF_AUTH_MODE] = auth_mode

        cached_info = _cacheable_info(info)
        if data.get(CONF_CACHED_INFO) != cached_info:
            data[CONF_CACHED_INFO] = cached_info

        if data != entry.data:
            self.hass.config_entries.async_update_entry(entry, data=data)

        if reload_needed:
            self.hass.async_create_task(
                self.hass.config_entries.async_reload(entry.entry_id)
            )

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Handle manual setup."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = str(user_input[CONF_HOST]).strip()
            port = int(user_input.get(CONF_PORT, DEFAULT_PORT))
            token = _token_from_input(user_input)

            try:
                info = await _async_retry_setup_call(
                    "manual setup",
                    host,
                    port,
                    lambda: _async_validate_device(self.hass, host, port, token or None),
                )
            except UnsupportedProduct:
                errors["base"] = "unsupported_product"
            except SmartGateAuthError:
                errors["base"] = "invalid_auth"
            except SmartGateApiError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected Smart Gate setup error")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(info[CONF_DEVICE_ID])
                self._abort_if_unique_id_configured()
                return self._create_config_entry(info, host, port, token, AUTH_MODE_MANUAL)

        return self.async_show_form(step_id="user", data_schema=self._user_schema(), errors=errors)

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> FlowResult:
        """Start reauth when the local API returns 401."""
        self._reauth_entry = self._get_reauth_entry()
        if self._reauth_entry is None:
            return self.async_abort(reason="cannot_connect")
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Collect a replacement local API token."""
        if self._reauth_entry is None:
            return self.async_abort(reason="cannot_connect")

        errors: dict[str, str] = {}
        if user_input is not None:
            token = _token_from_input(user_input)
            data = dict(self._reauth_entry.data)
            try:
                info = await _async_validate_device(
                    self.hass,
                    data[CONF_HOST],
                    int(data.get(CONF_PORT, DEFAULT_PORT)),
                    token or None,
                )
            except SmartGateAuthError:
                errors["base"] = "invalid_auth"
            except UnsupportedProduct:
                errors["base"] = "unsupported_product"
            except SmartGateApiError:
                errors["base"] = "cannot_connect"
            else:
                if token:
                    data[CONF_TOKEN] = token
                else:
                    data.pop(CONF_TOKEN, None)
                data[CONF_CACHED_INFO] = _cacheable_info(info)
                self.hass.config_entries.async_update_entry(self._reauth_entry, data=data)
                await self.hass.config_entries.async_reload(self._reauth_entry.entry_id)
                return self.async_abort(reason="reauth_successful")

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=self._token_schema(required=True),
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
                vol.Optional(CONF_TOKEN): TOKEN_SELECTOR,
            }
        )

    @staticmethod
    def _token_schema(required: bool) -> vol.Schema:
        """Return a token-only schema."""
        key = vol.Required(CONF_TOKEN) if required else vol.Optional(CONF_TOKEN)
        return vol.Schema({key: TOKEN_SELECTOR})


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
        current_interval = int(self._entry.options.get(CONF_POLL_INTERVAL, SCAN_INTERVAL_SECONDS))
        current_host = str(self._entry.data.get(CONF_HOST, ""))
        current_port = int(self._entry.data.get(CONF_PORT, DEFAULT_PORT))
        current_token = _stored_token(self._entry.data)

        if user_input is not None:
            new_host = str(user_input.get(CONF_HOST, current_host)).strip()
            new_port = int(user_input.get(CONF_PORT, current_port))
            entered_token = _token_from_input(user_input)
            new_token = entered_token if entered_token else current_token
            new_name = str(user_input.get(CONF_FRIENDLY_NAME_OVERRIDE, "")).strip()
            poll_interval = int(user_input.get(CONF_POLL_INTERVAL, current_interval))
            options = dict(self._entry.options)
            options[CONF_POLL_INTERVAL] = poll_interval
            data = dict(self._entry.data)

            try:
                validated_info = await _async_validate_device(self.hass, new_host, new_port, new_token or None)
            except SmartGateAuthError:
                errors["base"] = "invalid_auth"
            except UnsupportedProduct:
                errors["base"] = "unsupported_product"
            except SmartGateApiError:
                errors["base"] = "cannot_connect"
            else:
                if validated_info[CONF_DEVICE_ID] != self._entry.data[CONF_DEVICE_ID]:
                    errors["base"] = "cannot_connect"

            if not errors:
                session = async_get_clientsession(self.hass)
                api = SmartGateApiClient(session, new_host, new_port, new_token or None)
                name_changed = bool(new_name and new_name != current_name)

                if name_changed:
                    try:
                        response = await api.set_name(new_name)
                    except SmartGateAuthError:
                        errors["base"] = "invalid_auth"
                    except SmartGateRenameNotSupported:
                        errors["base"] = "rename_not_supported"
                    except SmartGateApiError:
                        errors["base"] = "cannot_update_name"
                    else:
                        applied_name = response.get("friendly_name", new_name)
                        validated_info = dict(validated_info)
                        validated_info["friendly_name"] = applied_name
                        options[CONF_FRIENDLY_NAME_OVERRIDE] = applied_name
                        self.hass.config_entries.async_update_entry(self._entry, title=applied_name)
                elif not new_name:
                    options.pop(CONF_FRIENDLY_NAME_OVERRIDE, None)

            if not errors:
                data[CONF_HOST] = new_host
                data[CONF_PORT] = new_port
                if new_token:
                    data[CONF_TOKEN] = new_token
                else:
                    data.pop(CONF_TOKEN, None)
                data[CONF_CACHED_INFO] = _cacheable_info(validated_info)
                self.hass.config_entries.async_update_entry(
                    self._entry,
                    title=new_name or current_name,
                    data=data,
                )
                return self.async_create_entry(title="", data=options)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_HOST, default=current_host): str,
                    vol.Optional(CONF_PORT, default=current_port): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=1, max=65535),
                    ),
                    vol.Optional(CONF_TOKEN): TOKEN_SELECTOR,
                    vol.Optional(CONF_FRIENDLY_NAME_OVERRIDE, default=current_name): str,
                    vol.Optional(CONF_POLL_INTERVAL, default=current_interval): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_SCAN_INTERVAL_SECONDS, max=MAX_SCAN_INTERVAL_SECONDS),
                    ),
                }
            ),
            errors=errors,
        )
