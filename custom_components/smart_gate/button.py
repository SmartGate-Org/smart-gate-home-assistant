"""Button platform for Smart Gate devices."""

from __future__ import annotations

from homeassistant.components.button import ButtonDeviceClass, ButtonEntity
from homeassistant.const import EntityCategory
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
    """Set up Smart Gate buttons."""
    async_add_entities([SmartGateIdentifyButton(entry)])


class SmartGateIdentifyButton(SmartGateEntity, ButtonEntity):
    """Identify button for a Smart Gate device."""

    _attr_device_class = ButtonDeviceClass.IDENTIFY
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:crosshairs-question"
    _attr_name = "Identify"

    def __init__(self, entry: SmartGateConfigEntry) -> None:
        """Initialize the identify button."""
        super().__init__(entry)
        self._attr_unique_id = f"{self.device_id}_identify"

    async def async_press(self) -> None:
        """Press the identify button."""
        try:
            await self.api.identify()
        except SmartGateApiError as err:
            raise HomeAssistantError(f"Smart Gate identify failed: {err}") from err
