"""Binary diagnostic sensors for Smart Gate devices."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import SmartGateConfigEntry
from .entity import SmartGateEntity


@dataclass(frozen=True, kw_only=True)
class SmartGateBinarySensorDescription(BinarySensorEntityDescription):
    """Description for a Smart Gate binary diagnostic sensor."""

    value_fn: Callable[[SmartGateConfigEntry, dict[str, Any]], bool | None]


BINARY_SENSOR_DESCRIPTIONS: tuple[SmartGateBinarySensorDescription, ...] = (
    SmartGateBinarySensorDescription(
        key="cloud_connection",
        translation_key="cloud_connection",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda entry, state: _cloud_connected(state),
    ),
    SmartGateBinarySensorDescription(
        key="local_api",
        translation_key="local_api",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda entry, state: entry.runtime_data.coordinator.last_update_success,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SmartGateConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Smart Gate binary diagnostic sensors."""
    async_add_entities(
        SmartGateBinarySensor(entry, description)
        for description in BINARY_SENSOR_DESCRIPTIONS
    )


def _cloud_connected(state: dict[str, Any]) -> bool | None:
    """Return cloud/WSS connectivity from firmware state."""
    connected = state.get("wss_connected")
    if isinstance(connected, bool):
        return connected

    status = state.get("wss_status")
    if isinstance(status, str):
        return status == "connected"

    return None


class SmartGateBinarySensor(SmartGateEntity, BinarySensorEntity):
    """Binary diagnostic sensor for a Smart Gate device."""

    entity_description: SmartGateBinarySensorDescription

    def __init__(
        self,
        entry: SmartGateConfigEntry,
        description: SmartGateBinarySensorDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(entry)
        self.entity_description = description
        self._attr_unique_id = f"{self.device_id}_{description.key}"

    @property
    def available(self) -> bool:
        """Return whether this binary sensor has a meaningful state."""
        if self.entity_description.key == "local_api":
            return True

        state = self.coordinator.data or {}
        return self.coordinator.last_update_success and _cloud_connected(state) is not None

    @property
    def is_on(self) -> bool | None:
        """Return the binary sensor state."""
        return self.entity_description.value_fn(
            self.entry,
            self.coordinator.data or {},
        )
