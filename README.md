<p align="center">
  <img src="custom_components/smart_gate/brand/logo.png" alt="Smart Gate" width="160">
</p>

<h1 align="center">Smart Gate Home Assistant Integration</h1>

<p align="center">
  Local control, discovery, and relay management for Smart Gate devices.
</p>

# Smart Gate Home Assistant Integration

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://www.hacs.xyz/)
![Version](https://img.shields.io/badge/version-v0.5.0-blue)
![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2026.4%2B-18BCF2)

Local Home Assistant integration for Smart Gate devices using LAN discovery and local HTTP control.

This release supports SG-Load-Box with local polling, Zeroconf discovery, local HTTP authentication, one switch per relay channel, device identification, friendly naming, and runtime diagnostics.

## Supported Products

| Product | Status |
| --- | --- |
| SG-Load-Box | Supported |
| SG-MiniBox | Planned |
| SG-Touch-Box | Planned |
| SG-Presence-Radar | Planned |
| SG-Temp-Hum | Planned |

## Features

- Local control without cloud dependency for Home Assistant control.
- Zeroconf/mDNS discovery using `_smartgate._tcp.local`.
- Manual IP/hostname fallback.
- Local API token support for protected firmware endpoints.
- Temporary MVP setup where the Local API Token can be the device Wi-Fi password.
- Reauth flow when firmware returns `401 Unauthorized`.
- Options Flow for host, port, Local API Token, device name, and polling interval.
- One switch entity per Load Box channel.
- Identify button for locating the physical device.
- Runtime diagnostics: Local API, Cloud connection, Wi-Fi RSSI, IP address, last command source, last seen, uptime, free heap, firmware version, and API version.
- Friendly device naming from firmware `friendly_name`, or `Smart Gate Load Box <short_id>` fallback.
- Boot physical-state safety handled by compatible SG-Load-Box firmware.

## Requirements

- Home Assistant Core 2026.4 or newer.
- HACS 2.0 or newer is recommended.
- Smart Gate SG-Load-Box firmware with Local HTTP API v1.
- Home Assistant and the device on the same LAN/VLAN, or otherwise routable.
- TCP port `8080` reachable from Home Assistant.
- mDNS available for auto-discovery, or manual setup by IP address.
- If firmware auth is required, the Local API Token or current device Wi-Fi password.

## HACS Installation

1. Open HACS in Home Assistant.
2. Go to Integrations.
3. Open the three-dot menu and select Custom repositories.
4. Add this repository URL:

   ```text
   https://github.com/SmartGate-Org/smart-gate-home-assistant
   ```

5. Select category Integration.
6. Download Smart Gate.
7. Restart Home Assistant.
8. Go to Settings > Devices & services.
9. Smart Gate should appear as a discovered device. Click Add.
10. Enter the Local API Token / Wi-Fi Password if prompted.

## Manual Installation

1. Copy `custom_components/smart_gate` into your Home Assistant configuration folder:

   ```text
   /homeassistant/custom_components/smart_gate
   ```

2. Restart Home Assistant.
3. Go to Settings > Devices & services.
4. Select Add Integration and search for Smart Gate.

## Setup

1. Power on the Smart Gate device.
2. Add the device to Wi-Fi using the Smart Gate mobile app or supported provisioning flow.
3. Make sure Home Assistant can reach the device on the same LAN/VLAN.
4. Install the integration through HACS or manual copy.
5. Restart Home Assistant.
6. Accept the discovered Smart Gate device, or add it manually with IP/hostname and port `8080`.
7. Enter Local API Token / Wi-Fi Password when firmware auth is enabled.
8. Select the Area during setup if desired.
9. Press Identify to locate the physical device.
10. Rename the physical/network device from Smart Gate integration Options if needed.
11. Rename channel entities in Home Assistant if you want dashboard-specific labels.

## Local Auth

The integration always calls public `GET /v1/info` first. When a token is provided, setup also validates protected `GET /v1/state` using:

```text
Authorization: Bearer <token>
```

For the current firmware MVP, the token can be the device Wi-Fi password. This is temporary. Later firmware and app releases should replace it with an app-generated local token.

The token is stored in the Home Assistant config entry and is never placed in device names, titles, diagnostics, or log messages by this integration.

## Diagnostics

- Local API shows whether Home Assistant can reach the device locally.
- Cloud connection shows the firmware-reported WSS/cloud state.
- Wi-Fi RSSI helps identify poor 2.4 GHz coverage.
- IP address shows the current firmware-reported address, with HA host fallback.
- Last command source shows whether the latest relay state came from `physical_startup`, `mcp_input`, `local_http`, or `wss`.
- Last seen records the latest successful local poll.
- Free heap, uptime, firmware version, and API version help support and firmware compatibility checks.

If Cloud connection is offline but Local API is online, Home Assistant local control can still work.

## Troubleshooting

See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md).

Common checks:

- Confirm the device is powered on and connected to Wi-Fi.
- Open `http://DEVICE_IP:8080/v1/info` from a browser or terminal.
- If `/v1/state` returns `401`, update the integration Local API Token / Wi-Fi Password.
- Confirm the integration folder is exactly `custom_components/smart_gate`.
- Restart Home Assistant after installing or updating the integration.
- Hard refresh the browser if the Add Integration dialog or logo does not update.

## Security

Do not expose device port `8080` to the internet. Treat the Local API Token and Wi-Fi password as secrets.

The firmware currently supports a temporary Wi-Fi-password-as-local-token mode for MVP deployments. The final production model should use an app-generated local token and disable Wi-Fi password token acceptance.

## Development Status

`v0.5.0` is the local-auth and branding polish release for SG-Load-Box local control.

Known limitations:

- SG-Load-Box is the only officially supported product in this release.
- The temporary Wi-Fi-password token mode is not the final production security model.
- This is a HACS custom integration, not an official Home Assistant Core integration.

## License

MIT License. See [LICENSE](LICENSE).
