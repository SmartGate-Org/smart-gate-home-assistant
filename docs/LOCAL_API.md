# Local API Guide

Smart Gate devices expose a local HTTP API for Home Assistant control and diagnostics. The default local API port is:

```text
8080
```

Use placeholders when testing or documenting commands:

- `<DEVICE_IP>` for the Smart Gate device IP address
- `<LOCAL_API_TOKEN>` for the Local API Token

Do not share real tokens or Wi-Fi passwords in screenshots, logs, or support requests.

## Authentication

The integration sends the configured token as:

```text
Authorization: Bearer <token>
```

Current MVP firmware may use the device Wi-Fi password as the Local API Token. Future firmware and app versions should use a dedicated local token.

## Public Endpoints

These endpoints can be used for basic device discovery and health checks:

| Endpoint | Purpose |
| --- | --- |
| `GET /v1/info` | Device identity and capabilities |
| `GET /v1/health` | Basic health and connectivity information |

Example:

```text
http://<DEVICE_IP>:8080/v1/info
```

## Protected Endpoints

These endpoints may require the Local API Token:

| Endpoint | Purpose |
| --- | --- |
| `GET /v1/state` | Current relay state and runtime diagnostics |
| `POST /v1/control` | Set relay channel states |
| `POST /v1/identify` | Request device identify behavior |
| `POST /v1/config/name` | Update the device friendly name when supported |

Example protected request:

```bash
curl -H "Authorization: Bearer <LOCAL_API_TOKEN>" http://<DEVICE_IP>:8080/v1/state
```

## State

`GET /v1/state` returns the current relay state and related diagnostics. A typical relay state uses this format:

```json
{
  "relays": "0-0-0-0-0-0",
  "relay_mask": 0,
  "channels": 6
}
```

## Control

`POST /v1/control` sets relay channels with a full relay string.

Example request body:

```json
{
  "request_id": "ha-example",
  "relays": "1-1-0-0-0-0"
}
```

Example curl command:

```bash
curl -X POST http://<DEVICE_IP>:8080/v1/control \
  -H "Authorization: Bearer <LOCAL_API_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"request_id":"ha-example","relays":"1-1-0-0-0-0"}'
```

## Identify

`POST /v1/identify` asks the device to identify itself when supported by the device firmware and hardware.

```bash
curl -X POST http://<DEVICE_IP>:8080/v1/identify \
  -H "Authorization: Bearer <LOCAL_API_TOKEN>"
```

## Rename

`POST /v1/config/name` updates the device friendly name when supported.

Example request body:

```json
{
  "request_id": "ha-name-example",
  "friendly_name": "Garage Load Box"
}
```

Older firmware may not support local rename. In that case, use the device name shown by Home Assistant or update the name from the Smart Gate app when available.
