"""Switch platform for Smart Gate relay channels."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import SmartGateConfigEntry
from .api import SmartGateApiError
from .entity import SmartGateEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SmartGateConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Smart Gate relay switches."""
    runtime_data = entry.runtime_data
    channels = runtime_data.coordinator.channels or int(
        runtime_data.info.get("channels", 0)
    )

    async_add_entities(
        SmartGateRelaySwitch(entry, channel_index)
        for channel_index in range(channels)
    )


class SmartGateRelaySwitch(
    SmartGateEntity,
    SwitchEntity,
):
    """Representation of one SG-Load-Box relay channel."""

    _attr_has_entity_name = True
    _attr_device_class = SwitchDeviceClass.OUTLET
    _attr_icon = "mdi:electric-switch"

    def __init__(
        self,
        entry: SmartGateConfigEntry,
        channel_index: int,
    ) -> None:
        """Initialize the relay switch."""
        super().__init__(entry)
        self._channel_index = channel_index
        self._channel_number = channel_index + 1

        self._channel_label = f"Channel {self._channel_number}"
        self._attr_name = self._channel_label
        self._attr_unique_id = f"{self.device_id}_ch_{self._channel_number}"

    @property
    def is_on(self) -> bool | None:
        """Return whether the relay channel is on."""
        if not self.available:
            return None
        return self.coordinator.is_channel_on(self._channel_index)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra diagnostics for the relay channel."""
        data = self.coordinator.data or {}
        return {
            "channel": self._channel_number,
            "channel_label": self._channel_label,
            "profile": self.info.get("profile"),
            "product": self.product,
            "relay_mask": data.get("relay_mask"),
            "heap_free": data.get("heap_free"),
            "uptime": data.get("uptime"),
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on this relay channel."""
        await self._async_set_channel(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off this relay channel."""
        await self._async_set_channel(False)

    async def _async_set_channel(self, turn_on: bool) -> None:
        """Update one channel through the coordinator command manager."""
        try:
            await self.coordinator.async_set_channel_state(
                self._channel_index,
                turn_on,
            )
        except SmartGateApiError as err:
            raise HomeAssistantError(f"Smart Gate relay command failed: {err}") from err
