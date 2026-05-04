"""Async local HTTP client for Smart Gate devices."""

from __future__ import annotations

import asyncio
import logging
from typing import Any
from uuid import uuid4

import aiohttp
from yarl import URL

_LOGGER = logging.getLogger(__name__)

REQUEST_TIMEOUT_SECONDS = 5


class SmartGateApiError(Exception):
    """Raised when a Smart Gate device request fails."""

    def __init__(self, message: str, status: int | None = None) -> None:
        """Initialize the API error."""
        super().__init__(message)
        self.status = status


class SmartGateRenameNotSupported(SmartGateApiError):
    """Raised when firmware does not support local rename."""


def parse_relays(relays: str, channels: int) -> list[bool]:
    """Parse a relay state string into booleans."""
    if channels <= 0:
        raise SmartGateApiError("invalid channel count")

    parts = relays.split("-")
    if len(parts) != channels or any(part not in {"0", "1"} for part in parts):
        raise SmartGateApiError("invalid relay state format")

    return [part == "1" for part in parts]


def build_relays_string(current: str, channel_index: int, on: bool) -> str:
    """Build a new relay string by changing one zero-based channel."""
    parts = current.split("-")
    if channel_index < 0 or channel_index >= len(parts):
        raise SmartGateApiError("relay channel is out of range")
    if any(part not in {"0", "1"} for part in parts):
        raise SmartGateApiError("invalid relay state format")

    parts[channel_index] = "1" if on else "0"
    return "-".join(parts)


class SmartGateApiClient:
    """Client for the SG-Load-Box local HTTP API."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        port: int = 8080,
    ) -> None:
        """Initialize the API client."""
        self._session = session
        self.host = host
        self.port = port
        self._base_url = URL.build(scheme="http", host=host, port=port)

    async def get_info(self) -> dict[str, Any]:
        """Return device information."""
        data = await self._request("GET", "/v1/info")
        self._require_str(data, "product")
        self._require_str(data, "device_id")
        self._require_int(data, "channels")
        return data

    async def get_state(self) -> dict[str, Any]:
        """Return current relay state."""
        data = await self._request("GET", "/v1/state")
        self._require_str(data, "relays")
        self._require_int(data, "relay_mask")
        self._require_int(data, "channels")
        parse_relays(data["relays"], data["channels"])
        return data

    async def set_relays(
        self,
        relays: str,
        request_id: str | None = None,
    ) -> dict[str, Any]:
        """Set all relay channels with an absolute relay string."""
        if not relays or any(part not in {"0", "1"} for part in relays.split("-")):
            raise SmartGateApiError("invalid relay command format")

        payload = {
            "request_id": request_id or f"ha-{uuid4().hex}",
            "relays": relays,
        }
        data = await self._request("POST", "/v1/control", json=payload)
        if data.get("ok") is False:
            raise SmartGateApiError("device rejected relay command")
        self._require_str(data, "actual_relays")
        return data

    async def identify(self) -> dict[str, Any]:
        """Ask the device to identify itself."""
        return await self._request("POST", "/v1/identify")

    async def set_name(
        self,
        friendly_name: str,
        request_id: str | None = None,
    ) -> dict[str, Any]:
        """Set the device friendly name through the local API."""
        friendly_name = friendly_name.strip()
        if not friendly_name:
            raise SmartGateApiError("device name cannot be empty")

        payload = {
            "request_id": request_id or f"ha-name-{uuid4().hex[:12]}",
            "friendly_name": friendly_name,
        }
        try:
            data = await self._request("POST", "/v1/config/name", json=payload)
        except SmartGateApiError as err:
            if err.status == 404:
                raise SmartGateRenameNotSupported(
                    "firmware does not support local rename", status=404
                ) from err
            raise

        if data.get("ok") is False:
            raise SmartGateApiError("device rejected name update")
        self._require_str(data, "friendly_name")
        return data

    async def health(self) -> dict[str, Any]:
        """Return device health data."""
        return await self._request("GET", "/v1/health")

    async def _request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Perform an HTTP request and decode a JSON object response."""
        url = self._base_url.join(URL(path))
        timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT_SECONDS)

        try:
            async with self._session.request(
                method,
                url,
                timeout=timeout,
                **kwargs,
            ) as response:
                if response.status < 200 or response.status >= 300:
                    body = await response.text()
                    raise SmartGateApiError(
                        f"{method} {path} failed with HTTP {response.status}: {body[:120]}",
                        status=response.status,
                    )

                data = await response.json(content_type=None)
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise SmartGateApiError(f"{method} {path} failed: {err}") from err
        except ValueError as err:
            raise SmartGateApiError(f"{method} {path} returned invalid JSON") from err

        if not isinstance(data, dict):
            raise SmartGateApiError(f"{method} {path} returned non-object JSON")

        return data

    @staticmethod
    def _require_str(data: dict[str, Any], key: str) -> None:
        """Validate a required string field."""
        if not isinstance(data.get(key), str) or data[key] == "":
            raise SmartGateApiError(f"missing or invalid '{key}'")

    @staticmethod
    def _require_int(data: dict[str, Any], key: str) -> None:
        """Validate a required integer field."""
        if not isinstance(data.get(key), int):
            raise SmartGateApiError(f"missing or invalid '{key}'")
