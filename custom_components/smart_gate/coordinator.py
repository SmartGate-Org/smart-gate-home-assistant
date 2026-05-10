"""Data coordinator for Smart Gate devices."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta, timezone
import logging
from typing import Any
from uuid import uuid4

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    SmartGateApiClient,
    SmartGateApiError,
    SmartGateAuthError,
    parse_relays,
)
from .const import INFO_REFRESH_INTERVAL_UPDATES

_LOGGER = logging.getLogger(__name__)

RELAY_COMMAND_DEBOUNCE_SECONDS = 0.15

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
        self._relay_command_lock = asyncio.Lock()
        self._desired_relay_mask: int | None = None
        self._confirmed_relay_mask: int | None = None
        self._pending_relay_states: dict[int, bool] = {}
        self._pending_command_task: asyncio.Task[None] | None = None
        self._pending_command_waiters: list[asyncio.Future[None]] = []
        self._relay_command_generation = 0
        self._relay_command_active = False

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch current device state."""
        async with self._relay_command_lock:
            command_generation = self._relay_command_generation
            command_in_progress = self._relay_command_active or bool(
                self._pending_relay_states
            )

        try:
            state = await self.api.get_state()
            self.last_successful_update = datetime.now(timezone.utc)
            state["_last_seen"] = self.last_successful_update
            state["_local_api_online"] = True
            await self._async_check_state_shape(state)
            await self._async_refresh_info_if_due()
            async with self._relay_command_lock:
                state = self._state_with_command_overlay(
                    state,
                    command_generation,
                    command_in_progress,
                )
            return state
        except SmartGateAuthError as err:
            raise ConfigEntryAuthFailed("Invalid Smart Gate local API token") from err
        except SmartGateApiError as err:
            raise UpdateFailed(str(err)) from err

    async def async_try_initial_refresh(self) -> bool:
        """Try one startup refresh without preventing offline setup."""
        try:
            data = await self._async_update_data()
        except ConfigEntryAuthFailed:
            raise
        except UpdateFailed:
            self._set_expected_channels_from_info()
            self.last_update_success = False
            return False

        self.last_update_success = True
        self.async_set_updated_data(data)
        return True

    def _set_expected_channels_from_info(self) -> None:
        """Use cached info as expected shape when loading offline."""
        channels = self.info.get("channels")
        if isinstance(channels, int) and channels > 0:
            self._expected_channels = channels

    async def async_set_channel_state(
        self,
        channel_index: int,
        is_on: bool,
    ) -> None:
        """Set one relay channel through the device-level command manager."""
        waiter: asyncio.Future[None] = asyncio.get_running_loop().create_future()

        async with self._relay_command_lock:
            channels = self._channel_count()
            if channels <= 0:
                raise SmartGateApiError("invalid channel count")
            if channel_index < 0 or channel_index >= channels:
                raise SmartGateApiError("relay channel is out of range")

            desired_mask = self._desired_relay_mask
            if desired_mask is None:
                desired_mask = self._current_relay_mask(channels)
            if self._confirmed_relay_mask is None:
                self._confirmed_relay_mask = desired_mask

            if is_on:
                desired_mask |= 1 << channel_index
            else:
                desired_mask &= ~(1 << channel_index)
            desired_mask &= self._relay_mask_limit(channels)

            self._desired_relay_mask = desired_mask
            self._pending_relay_states[channel_index] = is_on
            self._pending_command_waiters.append(waiter)
            self._relay_command_generation += 1
            self._apply_relay_mask(desired_mask, channels)

            if self._pending_command_task is None or self._pending_command_task.done():
                self._pending_command_task = self.hass.async_create_task(
                    self._async_relay_command_worker()
                )

        await waiter

    async def _async_relay_command_worker(self) -> None:
        """Batch and serialize relay commands for this device."""
        current_waiters: list[asyncio.Future[None]] = []
        try:
            while True:
                await asyncio.sleep(RELAY_COMMAND_DEBOUNCE_SECONDS)

                async with self._relay_command_lock:
                    if not self._pending_relay_states:
                        self._pending_command_task = None
                        return

                    channels = self._channel_count()
                    desired_mask = self._desired_relay_mask
                    if channels <= 0 or desired_mask is None:
                        error = SmartGateApiError("Smart Gate relay state is unavailable")
                        waiters = self._pop_all_pending_waiters()
                        self._pending_command_task = None
                        self._restore_confirmed_relay_mask(channels)
                    else:
                        error = None
                        waiters = self._pending_command_waiters
                        current_waiters = waiters
                        self._pending_command_waiters = []
                        self._pending_relay_states.clear()
                        self._relay_command_active = True
                        generation = self._relay_command_generation
                        requested_relays = self._mask_to_relays_string(
                            desired_mask,
                            channels,
                        )

                if error is not None:
                    self._set_waiter_exceptions(waiters, error)
                    self._schedule_refresh()
                    return

                response: dict[str, Any] | None = None
                actual_mask: int | None = None
                try:
                    request_id = f"ha-{uuid4().hex[:12]}"
                    response = await self.api.set_relays(
                        requested_relays,
                        request_id=request_id,
                    )
                    actual_relays = response.get("actual_relays")
                    if actual_relays != requested_relays:
                        raise SmartGateApiError(
                            "Smart Gate relay command did not reach the requested state"
                        )
                    actual_mask = self._relays_string_to_mask(actual_relays, channels)
                    response_mask = response.get("relay_mask")
                    if isinstance(response_mask, int):
                        response_mask &= self._relay_mask_limit(channels)
                        if response_mask != actual_mask:
                            raise SmartGateApiError(
                                "device returned inconsistent relay command state"
                            )
                except SmartGateApiError as err:
                    command_error = err
                except Exception:
                    command_error = SmartGateApiError(
                        "Smart Gate relay command failed"
                    )
                else:
                    command_error = None

                async with self._relay_command_lock:
                    self._relay_command_active = False
                    if command_error is None and actual_mask is not None:
                        self._confirmed_relay_mask = actual_mask
                        if generation == self._relay_command_generation:
                            self._desired_relay_mask = actual_mask
                            self._apply_relay_mask(
                                actual_mask,
                                channels,
                                response=response,
                            )
                        has_more = bool(self._pending_relay_states)
                        if not has_more:
                            self._pending_command_task = None
                    else:
                        waiters.extend(self._pop_all_pending_waiters())
                        self._restore_confirmed_relay_mask(channels)
                        self._pending_command_task = None
                        has_more = False

                if command_error is not None:
                    self._set_waiter_exceptions(waiters, command_error)
                    current_waiters = []
                    self._schedule_refresh()
                    return

                self._set_waiter_results(waiters)
                current_waiters = []
                self._schedule_refresh()
                if not has_more:
                    return
        except asyncio.CancelledError:
            raise
        except Exception as err:  # pragma: no cover - defensive task cleanup
            command_error = SmartGateApiError("Smart Gate relay command failed")
            async with self._relay_command_lock:
                waiters = current_waiters
                waiters.extend(self._pop_all_pending_waiters())
                self._relay_command_active = False
                self._pending_command_task = None
                self._restore_confirmed_relay_mask(self._channel_count())
            self._set_waiter_exceptions(waiters, command_error)
            self._schedule_refresh()
            _LOGGER.debug("[Smart Gate] Relay command worker failed: %s", err)

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
        try:
            new_info = await self.api.get_info()
        except SmartGateApiError:
            return

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

    def _channel_count(self) -> int:
        """Return the best known relay channel count."""
        data = self.data or {}
        channels = data.get("channels")
        if isinstance(channels, int) and channels > 0:
            return channels

        channels = self.info.get("channels")
        return channels if isinstance(channels, int) and channels > 0 else 0

    def _current_relay_mask(self, channels: int) -> int:
        """Return the current relay mask from optimistic or coordinator state."""
        if self._desired_relay_mask is not None:
            return self._desired_relay_mask & self._relay_mask_limit(channels)

        data = self.data or {}
        relays = data.get("relays")
        if isinstance(relays, str):
            return self._relays_string_to_mask(relays, channels)

        relay_mask = data.get("relay_mask")
        if isinstance(relay_mask, int):
            return relay_mask & self._relay_mask_limit(channels)

        raise SmartGateApiError("Smart Gate relay state is unavailable")

    def _state_with_command_overlay(
        self,
        state: dict[str, Any],
        command_generation: int,
        command_in_progress: bool,
    ) -> dict[str, Any]:
        """Protect optimistic command state from stale polling responses."""
        channels = state.get("channels")
        if not isinstance(channels, int) or channels <= 0:
            return state

        command_changed = command_generation != self._relay_command_generation
        command_active = self._relay_command_active or bool(self._pending_relay_states)
        if (
            command_in_progress
            or command_changed
            or command_active
        ) and self._desired_relay_mask is not None:
            return self._state_with_relay_mask(state, self._desired_relay_mask, channels)

        self._confirmed_relay_mask = self._relay_mask_from_state(state, channels)
        self._desired_relay_mask = self._confirmed_relay_mask
        return state

    def _state_with_relay_mask(
        self,
        state: dict[str, Any],
        relay_mask: int,
        channels: int,
        response: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Return a state dict with relay fields replaced by a mask."""
        relay_mask &= self._relay_mask_limit(channels)
        new_state = dict(state)
        new_state["channels"] = channels
        new_state["relay_mask"] = relay_mask
        new_state["relays"] = self._mask_to_relays_string(relay_mask, channels)

        if response is not None:
            source = response.get("source")
            if isinstance(source, str):
                new_state["source"] = source
                new_state["last_command_source"] = source

        return new_state

    def _apply_relay_mask(
        self,
        relay_mask: int,
        channels: int,
        response: dict[str, Any] | None = None,
    ) -> None:
        """Optimistically update coordinator data with a relay mask."""
        if channels <= 0:
            return
        state = self._state_with_relay_mask(
            self.data or {},
            relay_mask,
            channels,
            response=response,
        )
        self.async_set_updated_data(state)

    def _restore_confirmed_relay_mask(self, channels: int) -> None:
        """Restore the last confirmed relay state after a command failure."""
        self._pending_relay_states.clear()
        self._desired_relay_mask = self._confirmed_relay_mask
        if self._confirmed_relay_mask is not None:
            self._apply_relay_mask(self._confirmed_relay_mask, channels)

    def _relay_mask_from_state(self, state: dict[str, Any], channels: int) -> int:
        """Return a relay mask from a state payload."""
        relays = state.get("relays")
        if isinstance(relays, str):
            return self._relays_string_to_mask(relays, channels)

        relay_mask = state.get("relay_mask")
        if isinstance(relay_mask, int):
            return relay_mask & self._relay_mask_limit(channels)

        raise SmartGateApiError("Smart Gate relay state is unavailable")

    @staticmethod
    def _relays_string_to_mask(relays: str, channels: int) -> int:
        """Convert a relay string into a relay mask."""
        states = parse_relays(relays, channels)
        relay_mask = 0
        for channel_index, is_on in enumerate(states):
            if is_on:
                relay_mask |= 1 << channel_index
        return relay_mask

    @staticmethod
    def _mask_to_relays_string(relay_mask: int, channels: int) -> str:
        """Convert a relay mask into the firmware relay string format."""
        return "-".join(
            "1" if relay_mask & (1 << channel_index) else "0"
            for channel_index in range(channels)
        )

    @staticmethod
    def _relay_mask_limit(channels: int) -> int:
        """Return a bit mask covering valid relay channels."""
        return (1 << channels) - 1

    def _pop_all_pending_waiters(self) -> list[asyncio.Future[None]]:
        """Clear and return all pending command waiters."""
        waiters = self._pending_command_waiters
        self._pending_command_waiters = []
        self._pending_relay_states.clear()
        return waiters

    @staticmethod
    def _set_waiter_results(waiters: list[asyncio.Future[None]]) -> None:
        """Resolve command waiters."""
        for waiter in waiters:
            if not waiter.done():
                waiter.set_result(None)

    @staticmethod
    def _set_waiter_exceptions(
        waiters: list[asyncio.Future[None]],
        error: SmartGateApiError,
    ) -> None:
        """Fail command waiters."""
        for waiter in waiters:
            if not waiter.done():
                waiter.set_exception(error)

    def _schedule_refresh(self) -> None:
        """Request a refresh without delaying service-call completion."""
        self.hass.async_create_task(self.async_request_refresh())
