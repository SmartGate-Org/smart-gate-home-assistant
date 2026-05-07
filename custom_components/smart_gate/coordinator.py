"""Data coordinator for Smart Gate devices."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta, timezone
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import SmartGateApiClient, SmartGateApiError, SmartGateAuthError
from .const import INFO_REFRESH_INTERVAL_UPDATES

_LOGGER = logging.getLogger(__name__)

InfoChangedCallback = Callable[[dict[str, Any], dict[str, Any]], Awaitable[None]]
ReloadCallback = Callable[[str], Awaitable[None]]


class SmartGateDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Poll SG-Load-Box state."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: SmartGateApiClient,
        info: dict[str, Any],
        poll_interval_seconds: int,
        info_changed_callback: InfoChangedCallback | None = None,
        reload_callback: ReloadCallback | None = None,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Smart Gate",
            update_interval=timedelta(seconds=poll_interval_seconds),
            always_update=False,
        )
        self.api = api
        self.info = info
        self._info_changed_callback = info_changed_callback
        self._reload_callback = reload_callback
        self._expected_channels = 0
        self._profile = info.get("profile")
        self._updates_until_info_refresh = INFO_REFRESH_INTERVAL_UPDATES
        self._reload_requested = False
        self.last_successful_update: datetime | None = None

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch current device state."""
        try:
            state = await self.api.get_state()
            self.last_successful_update = datetime.now(timezone.utc)
            state["_last_seen"] = self.last_successful_update
            state["_local_api_online"] = True
            await self._async_check_state_shape(state)
            await self._async_refresh_info_if_due()
            return state
        except SmartGateAuthError as err:
            raise ConfigEntryAuthFailed("Invalid Smart Gate local API token") from err
        except SmartGateApiError as err:
            raise UpdateFailed(str(err)) from err

    async def _async_check_state_shape(self, state: dict[str, Any]) -> None:
        """Reload the entry if the firmware reports a different channel count."""
        channels = state.get("channels")
        if isinstance(channels, int) and self._expected_channels == 0:
            self._expected_channels = channels
            return
        if (
            isinstance(channels, int)
            and self._expected_channels
            and channels != self._expected_channels
        ):
            old_channels = self._expected_channels
            self._expected_channels = channels
            await self._async_request_reload(
                f"channel count changed from {old_channels} to {channels}"
            )

    async def _async_refresh_info_if_due(self) -> None:
        """Periodically refresh /v1/info for name/profile changes."""
        self._updates_until_info_refresh -= 1
        if self._updates_until_info_refresh > 0:
            return

        self._updates_until_info_refresh = INFO_REFRESH_INTERVAL_UPDATES
        new_info = await self.api.get_info()
        old_info = dict(self.info)

        old_channels = self._expected_channels
        new_channels = new_info.get("channels")
        if isinstance(new_channels, int):
            self._expected_channels = new_channels

        old_profile = self._profile
        self._profile = new_info.get("profile")

        self.info.clear()
        self.info.update(new_info)

        if self._info_changed_callback is not None and new_info != old_info:
            await self._info_changed_callback(old_info, new_info)

        if (
            isinstance(new_channels, int)
            and old_channels
            and new_channels != old_channels
        ):
            await self._async_request_reload(
                f"channel count changed from {old_channels} to {new_channels}"
            )
        elif self._profile != old_profile:
            _LOGGER.info(
                "[Smart Gate] Device profile changed from %s to %s",
                old_profile,
                self._profile,
            )

    async def _async_request_reload(self, reason: str) -> None:
        """Ask Home Assistant to reload this entry once."""
        if self._reload_requested:
            return

        self._reload_requested = True
        _LOGGER.info("[Smart Gate] %s, reloading config entry", reason)
        if self._reload_callback is not None:
            await self._reload_callback(reason)

    @property
    def channels(self) -> int:
        """Return the channel count."""
        if not self.data:
            return 0
        channels = self.data.get("channels")
        return channels if isinstance(channels, int) else 0

    @property
    def relays_string(self) -> str:
        """Return the relay state string."""
        if not self.data:
            return ""
        relays = self.data.get("relays")
        return relays if isinstance(relays, str) else ""

    @property
    def relay_mask(self) -> int:
        """Return the relay state mask."""
        if not self.data:
            return 0
        relay_mask = self.data.get("relay_mask")
        return relay_mask if isinstance(relay_mask, int) else 0

    def is_channel_on(self, channel_index_zero_based: int) -> bool:
        """Return whether a zero-based channel is currently on."""
        parts = self.relays_string.split("-")
        if channel_index_zero_based < 0 or channel_index_zero_based >= len(parts):
            return False
        return parts[channel_index_zero_based] == "1"
