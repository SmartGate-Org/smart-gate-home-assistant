# Local API

Smart Gate Home Assistant integration v0.5.0 uses the SG-Load-Box Local HTTP API. Fields marked optional may be missing on older firmware; the integration remains backward compatible where possible.

Default port:

```text
8080
```

## Authentication

Public endpoints:

- `GET /v1/info`
- `GET /v1/health`

Protected endpoints when firmware local auth is required:

- `GET /v1/state`
- `POST /v1/control`
- `POST /v1/identify`
- `POST /v1/config/name`

The integration sends the configured token as:

```text
Authorization: Bearer <token>
```

Firmware also accepts:

```text
X-SG-Local-Token: <token>
```

For the current MVP firmware, `<token>` may be the device Wi-Fi password. This is temporary and should later be replaced by an app-generated local token. The firmware does not expose the token through `/v1/info`, mDNS, BLE, UART logs, or diagnostics.

Unauthorized response:

```json
{"ok":false,"error":"unauthorized"}
```

Home Assistant maps HTTP `401` to `invalid_auth` during setup and to a reauth request at runtime.

## GET /v1/info

Returns static product and discovery metadata.

```json
{
  "product": "SG-Load-Box",
  "profile": "IO_PROFILE_6",
  "fw": "3.0.5",
  "device_id": "id-7a4c2c",
  "short_id": "7a4c2c",
  "friendly_name": "Smart-Gate-7a4c2c",
  "hostname": "Smart-Gate-7a4c2c",
  "api": 1,
  "port": 8080,
  "channels": 6,
  "capabilities": [
    "relay",
    "local_http",
    "mcp23017",
    "identify",
    "rename"
  ]
}
```

Required for setup:

- `product`
- `device_id`
- `channels`

Optional but used when present:

- `profile`
- `fw`
- `short_id`
- `friendly_name`
- `hostname`
- `api`
- `capabilities`

## GET /v1/state

Returns current relay state and runtime diagnostics. This endpoint may require auth.

```json
{
  "relays": "0-0-0-0-0-0",
  "relay_mask": 0,
  "cloud_shadow": "0-0-0-0-0-0",
  "cloud_shadow_mask": 0,
  "channels": 6,
  "source": "physical_startup",
  "last_command_source": "physical_startup",
  "uptime": 900,
  "heap_free": 41032,
  "wifi_connected": true,
  "wifi_rssi": -54,
  "ip_address": "192.168.1.83",
  "wss_connected": true,
  "wss_status": "connected",
  "startup_sync_done": true,
  "startup_cloud_publish_pending": false,
  "startup_cloud_publish_done": true,
  "last_command_at_ms": 123456,
  "last_state_publish_at_ms": 123999
}
```

Required for relay entities:

- `relays`
- `relay_mask`
- `channels`

Compatible firmware protects boot physical state by reading MCP/manual inputs at startup, publishing that state to cloud, and ignoring stale retained cloud switch state during the startup sync window.

## GET /v1/health

Returns compact health information. This endpoint is public.

```json
{
  "ok": true,
  "uptime": 900,
  "heap_free": 41032,
  "heap_min": 32768,
  "tasks": 5,
  "local_api": "online",
  "wifi": "connected",
  "wifi_connected": true,
  "wifi_rssi": -54,
  "ip_address": "192.168.1.83",
  "wss_connected": true,
  "wss_status": "connected",
  "startup_sync_done": true,
  "startup_cloud_publish_pending": false,
  "local_http": "running",
  "mdns": "running"
}
```

Home Assistant primarily polls `/v1/state` and does not need to poll `/v1/health` every cycle.

## POST /v1/control

Sets all relay channels with one full relay string. This endpoint may require auth.

Request:

```json
{
  "request_id": "ha-123",
  "relays": "1-1-1-0-0-0"
}
```

Response:

```json
{
  "ok": true,
  "request_id": "ha-123",
  "requested_relays": "1-1-1-0-0-0",
  "actual_relays": "1-1-1-0-0-0",
  "relay_mask": 7,
  "source": "local_http"
}
```

Home Assistant verifies `actual_relays` after control and refreshes state immediately.

## POST /v1/identify

Requests the device identify behavior. This endpoint may require auth.

```json
{
  "ok": true
}
```

The physical effect depends on firmware and hardware support.

## POST /v1/config/name

Optional endpoint for firmware that supports local rename. This endpoint may require auth.

Request:

```json
{
  "request_id": "ha-name-123",
  "friendly_name": "Bedroom Load Box"
}
```

Response:

```json
{
  "ok": true,
  "request_id": "ha-name-123",
  "friendly_name": "Bedroom Load Box",
  "hostname": "Bedroom-Load-Box",
  "source": "local_http"
}
```

Older firmware may return `404`. In that case the Home Assistant integration keeps working and shows a rename-not-supported message in Options.
