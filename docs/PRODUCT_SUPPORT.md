# Product Support

## Compatibility Table

| Product | Platform | Status | Entities | Notes |
| --- | --- | --- | --- | --- |
| SG-Load-Box | Local HTTP | Supported | Switches, Identify button, diagnostics | `IO_PROFILE_6` tested. Dynamic channel counts are supported when firmware reports correct `channels` and relay string length. |
| SG-MiniBox | Planned | Planned | Switches | Future local API validation required. |
| SG-Touch-Box | Planned | Planned | Switches | Future local API validation required. |
| SG-Presence-Radar | Planned | Planned | Binary sensors and sensors | Not implemented in v0.4.0. |
| SG-Temp-Hum | Planned | Planned | Sensors | Not implemented in v0.4.0. |

## SG-Load-Box Profiles

The integration creates one switch entity per channel reported by firmware.

Tested:

- `IO_PROFILE_6`

Supported by design but requiring runtime validation:

- `IO_PROFILE_8`
- `IO_PROFILE_12`
- `IO_PROFILE_16`
- Other firmware profiles that expose matching `channels`, `relays`, and `relay_mask` fields.

Existing switch unique IDs are preserved:

```text
{device_id}_ch_{channel_number}
```

## Firmware Requirements

Recommended firmware for v0.4.0:

- Local HTTP API v1.
- mDNS `_smartgate._tcp.local`.
- `/v1/info` with stable `device_id`.
- `/v1/state` with relay state and channel count.
- Compatible runtime diagnostics for the full v0.4.0 diagnostic entity set.
- Boot physical-state protection so MCP/manual startup state wins over stale retained cloud state.

Older firmware can still work for basic relay control if `/v1/info`, `/v1/state`, and `/v1/control` are available.
