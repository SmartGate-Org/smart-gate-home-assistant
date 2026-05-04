"""Smart Gate Home Assistant integration."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import device_registry as dr

from .api import SmartGateApiClient, SmartGateApiError
from .const import (
    CONF_DEVICE_ID,
    CONF_FRIENDLY_NAME_OVERRIDE,
    CONF_HOST,
    CONF_POLL_INTERVAL,
    CONF_PORT,
    CONF_PRODUCT,
    DEFAULT_PORT,
    DOMAIN,
    SCAN_INTERVAL_SECONDS,
)
from .coordinator import SmartGateDataUpdateCoordinator
from .entity import smart_gate_device_name

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.SENSOR,
    Platform.SWITCH,
]


@dataclass
class SmartGateRuntimeData:
    """Runtime objects for one Smart Gate config entry."""

    api: SmartGateApiClient
    coordinator: SmartGateDataUpdateCoordinator
    info: dict[str, Any]


SmartGateConfigEntry = ConfigEntry[SmartGateRuntimeData]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SmartGateConfigEntry,
) -> bool:
    """Set up Smart Gate from a config entry."""
    session = async_get_clientsession(hass)
    api = SmartGateApiClient(
        session,
        entry.data[CONF_HOST],
        int(entry.data.get(CONF_PORT, DEFAULT_PORT)),
    )

    try:
        info = await api.get_info()
    except SmartGateApiError as err:
        raise ConfigEntryNotReady(f"Smart Gate device is unavailable: {err}") from err

    await _async_sync_config_entry_title(hass, entry, info)

    poll_interval = int(
        entry.options.get(CONF_POLL_INTERVAL, SCAN_INTERVAL_SECONDS)
    )

    async def _info_changed_callback(
        old_info: dict[str, Any],
        new_info: dict[str, Any],
    ) -> None:
        old_name = smart_gate_device_name(
            old_info,
            entry.data[CONF_DEVICE_ID],
            entry.data[CONF_PRODUCT],
        )
        new_name = smart_gate_device_name(
            new_info,
            entry.data[CONF_DEVICE_ID],
            entry.data[CONF_PRODUCT],
        )
        if old_name != new_name:
            _LOGGER.info("[Smart Gate] Device friendly name changed to %s", new_name)
        await _async_sync_config_entry_title(hass, entry, new_info)
        _async_sync_device_registry_name(hass, entry, new_info)

    async def _reload_callback(reason: str) -> None:
        hass.async_create_task(hass.config_entries.async_reload(entry.entry_id))

    coordinator = SmartGateDataUpdateCoordinator(
        hass,
        api,
        info,
        poll_interval,
        info_changed_callback=_info_changed_callback,
        reload_callback=_reload_callback,
    )
    await coordinator.async_config_entry_first_refresh()

    runtime_data = SmartGateRuntimeData(api=api, coordinator=coordinator, info=info)
    entry.runtime_data = runtime_data
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = runtime_data
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _async_sync_device_registry_name(hass, entry, info)
    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: SmartGateConfigEntry,
) -> bool:
    """Unload a Smart Gate config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return unload_ok


async def _async_update_listener(
    hass: HomeAssistant,
    entry: SmartGateConfigEntry,
) -> None:
    """Reload the entry after options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def _async_sync_config_entry_title(
    hass: HomeAssistant,
    entry: SmartGateConfigEntry,
    info: dict[str, Any],
) -> None:
    """Update the integration-owned config entry title from firmware name."""
    if entry.options.get(CONF_FRIENDLY_NAME_OVERRIDE):
        return

    title = smart_gate_device_name(
        info,
        entry.data[CONF_DEVICE_ID],
        entry.data[CONF_PRODUCT],
    )
    if title != entry.title:
        hass.config_entries.async_update_entry(entry, title=title)


def _async_sync_device_registry_name(
    hass: HomeAssistant,
    entry: SmartGateConfigEntry,
    info: dict[str, Any],
) -> None:
    """Update integration-owned device registry metadata without touching user names."""
    device_registry = dr.async_get(hass)
    device = device_registry.async_get_device(
        identifiers={(DOMAIN, entry.data[CONF_DEVICE_ID])}
    )
    if device is None or device.name_by_user:
        return

    title = smart_gate_device_name(
        info,
        entry.data[CONF_DEVICE_ID],
        entry.data[CONF_PRODUCT],
    )
    if device.name != title:
        device_registry.async_update_device(device.id, name=title)
