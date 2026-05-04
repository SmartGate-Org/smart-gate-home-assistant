"""Diagnostic sensors for Smart Gate devices."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from . import SmartGateConfigEntry
from .const import CONF_HOST
from .entity import SmartGateEntity


@dataclass(frozen=True, kw_only=True)
class SmartGateSensorDescription(SensorEntityDescription):
    """Description for a Smart Gate diagnostic sensor."""

    value_fn: Callable[[dict[str, Any], dict[str, Any]], StateType]


SENSOR_DESCRIPTIONS: tuple[SmartGateSensorDescription, ...] = (
    SmartGateSensorDescription(
        key="uptime",
        translation_key="uptime",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda info, state: state.get("uptime"),
    ),
    SmartGateSensorDescription(
        key="heap_free",
        translation_key="heap_free",
        native_unit_of_measurement="B",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:memory",
        value_fn=lambda info, state: state.get("heap_free"),
    ),
    SmartGateSensorDescription(
        key="firmware_version",
        translation_key="firmware_version",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:chip",
        value_fn=lambda info, state: info.get("fw"),
    ),
    SmartGateSensorDescription(
        key="api_version",
        translation_key="api_version",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:api",
        value_fn=lambda info, state: info.get("api"),
    ),
    SmartGateSensorDescription(
        key="wifi_rssi",
        translation_key="wifi_rssi",
        native_unit_of_measurement="dBm",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda info, state: state.get("wifi_rssi"),
    ),
    SmartGateSensorDescription(
        key="ip_address",
        translation_key="ip_address",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:ip-network",
        value_fn=lambda info, state: state.get("ip_address"),
    ),
    SmartGateSensorDescription(
        key="last_command_source",
        translation_key="last_command_source",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:source-branch",
        value_fn=lambda info, state: state.get("last_command_source") or state.get("source"),
    ),
    SmartGateSensorDescription(
        key="last_seen",
        translation_key="last_seen",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:clock-check",
        value_fn=lambda info, state: state.get("_last_seen"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SmartGateConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Smart Gate diagnostic sensors."""
    info = entry.runtime_data.info
    state = entry.runtime_data.coordinator.data or {}

    async_add_entities(
        SmartGateDiagnosticSensor(entry, description)
        for description in SENSOR_DESCRIPTIONS
        if _sensor_exists(entry, description, info, state)
    )


def _sensor_exists(
    entry: SmartGateConfigEntry,
    description: SmartGateSensorDescription,
    info: dict[str, Any],
    state: dict[str, Any],
) -> bool:
    """Return whether this sensor should be created for the device."""
    if description.key in {"ip_address", "last_seen"}:
        return True
    return description.value_fn(info, state) is not None


class SmartGateDiagnosticSensor(SmartGateEntity, SensorEntity):
    """Diagnostic sensor for a Smart Gate device."""

    entity_description: SmartGateSensorDescription

    def __init__(
        self,
        entry: SmartGateConfigEntry,
        description: SmartGateSensorDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(entry)
        self.entity_description = description
        self._attr_unique_id = f"{self.device_id}_{description.key}"

    @property
    def native_value(self) -> StateType:
        """Return the current sensor value."""
        if self.entity_description.key == "ip_address":
            value = self.entity_description.value_fn(
                self.runtime_data.info,
                self.coordinator.data or {},
            )
            return value or self.entry.data.get(CONF_HOST)

        return self.entity_description.value_fn(
            self.runtime_data.info,
            self.coordinator.data or {},
        )
