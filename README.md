# Smart Gate Home Assistant Integration

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://www.hacs.xyz/)
![Version](https://img.shields.io/badge/version-v0.4.0-blue)
![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2026.4%2B-18BCF2)

Local Home Assistant integration for Smart Gate devices using LAN discovery and local HTTP control.

This release candidate supports SG-Load-Box with local polling, Zeroconf discovery, one switch per relay channel, device identification, friendly naming, and runtime diagnostics.

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
- One switch entity per Load Box channel.
- Identify button for locating the physical device.
- Runtime diagnostics: Local API, Cloud connection, Wi-Fi RSSI, IP address, last command source, last seen, uptime, free heap, firmware version, and API version.
- Friendly device naming from firmware `friendly_name` or `hostname`.
- Options Flow for device name and polling interval.
- Boot physical-state safety handled by compatible SG-Load-Box firmware.

## Requirements

- Home Assistant Core 2026.4 or newer.
- HACS 2.0 or newer is recommended.
- Smart Gate SG-Load-Box firmware with Local HTTP API v1.
- Home Assistant and the device on the same LAN/VLAN, or otherwise routable.
- TCP port `8080` reachable from Home Assistant.
- mDNS available for auto-discovery, or manual setup by IP address.

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
7. Select the Area during setup if desired.
8. Press Identify to locate the physical device.
9. Rename the physical/network device from Smart Gate integration Options if needed.
10. Rename channel entities in Home Assistant if you want dashboard-specific labels.

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
- Confirm the integration folder is exactly `custom_components/smart_gate`.
- Restart Home Assistant after installing or updating the integration.
- Hard refresh the browser if the Add Integration dialog does not show the custom integration.

## Security

The current local HTTP API is intended for trusted LAN/VLAN use. Do not expose device port `8080` to the internet.

Local authentication/token support is planned for a future firmware and integration release. Do not publish logs, screenshots, or issue reports containing tokens, Wi-Fi credentials, certificates, or private keys.

## Development Status

`v0.4.0` is the public HACS release candidate for SG-Load-Box local control.

Known limitations:

- SG-Load-Box is the only officially supported product in this release.
- Local HTTP auth is not implemented yet unless supported by future firmware.
- This is a HACS custom integration, not an official Home Assistant Core integration.

## License

MIT License. See [LICENSE](LICENSE).
