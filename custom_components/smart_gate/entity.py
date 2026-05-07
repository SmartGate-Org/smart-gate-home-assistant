"""Base entities for Smart Gate."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_DEVICE_ID,
    CONF_PRODUCT,
    DOMAIN,
    MANUFACTURER,
    PRODUCT_DISPLAY_NAMES,
)
from .coordinator import SmartGateDataUpdateCoordinator


def smart_gate_device_name(info: dict[str, Any], device_id: str, product: str) -> str:
    """Return the preferred display name for a Smart Gate device."""
    friendly_name = info.get("friendly_name")
    if isinstance(friendly_name, str) and friendly_name.strip():
        return friendly_name.strip()

    short_id = info.get("short_id")
    product_display = PRODUCT_DISPLAY_NAMES.get(product)
    if product_display and isinstance(short_id, str) and short_id.strip():
        return f"{product_display} {short_id.strip()}"

    hostname = info.get("hostname")
    if isinstance(hostname, str) and hostname.strip():
        return hostname.strip()

    if product_display:
        return f"{product_display} {device_id}"

    return f"{product} {device_id}"


class SmartGateEntity(CoordinatorEntity[SmartGateDataUpdateCoordinator]):
    """Base class for Smart Gate entities."""

    _attr_has_entity_name = True

    def __init__(self, entry: Any) -> None:
        """Initialize the base entity."""
        runtime_data = entry.runtime_data
        super().__init__(runtime_data.coordinator)

        self.entry = entry
        self.runtime_data = runtime_data
        self.api = runtime_data.api
        self.info = runtime_data.info
        self.device_id = entry.data[CONF_DEVICE_ID]
        self.product = entry.data[CONF_PRODUCT]

        profile = self.info.get("profile")
        model = f"{self.product} / {profile}" if profile else self.product
        self._device_name = smart_gate_device_name(
            self.info,
            self.device_id,
            self.product,
        )
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self.device_id)},
            name=self._device_name,
            manufacturer=MANUFACTURER,
            model=model,
            sw_version=self.info.get("fw"),
        )

    @property
    def available(self) -> bool:
        """Return whether the device is currently reachable."""
        return self.coordinator.last_update_success
