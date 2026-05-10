<p align="center">
  <img src="https://raw.githubusercontent.com/SmartGate-Org/smart-gate-home-assistant/main/brand/smart-gate.png" alt="Smart Gate" width="420">
</p>

# Smart Gate Home Assistant Integration

Official Home Assistant custom integration for Smart Gate local smart home devices.

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://www.hacs.xyz/)
![Version](https://img.shields.io/badge/version-v0.5.6-blue)
![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2026.4.0%2B-18BCF2)

Smart Gate for Home Assistant adds local LAN control, discovery, and entity management for compatible Smart Gate devices. It is designed for reliable local use while still allowing selected entities to be exposed to Google Assistant and Amazon Alexa through Home Assistant.

## Features

- Local LAN control
- Smart Gate Load Box support
- Zeroconf/mDNS discovery
- Secure local API token support
- Temporary Wi-Fi-password-as-token support for current firmware
- Google Assistant and Amazon Alexa support through Home Assistant
- Automatic recovery after device reboot
- Multi-relay command handling for voice and group control

## Supported Products

| Product | Status |
| --- | --- |
| SG-Load-Box | Supported |
| SG-MiniBox | Planned |
| SG-Touch-Box | Planned |
| SG-Presence-Radar | Planned |
| SG-Temp-Hum | Planned |

## Requirements

- Home Assistant 2026.4.0 or newer
- HACS 2.0.0 or newer
- Smart Gate device on the same local network as Home Assistant
- Local API enabled on the device firmware
- Local API token, or Wi-Fi password for current MVP firmware

## Installation

1. Open HACS in Home Assistant.
2. Go to HACS > Integrations.
3. Open the three-dot menu and select Custom repositories.
4. Add this repository URL:

   ```text
   https://github.com/SmartGate-Org/smart-gate-home-assistant
   ```

5. Choose Integration as the category.
6. Download Smart Gate.
7. Restart Home Assistant.
8. Open Settings > Devices & services.
9. Select Smart Gate from discovered devices, or choose Add Integration and search for Smart Gate.

See the full [Installation Guide](docs/INSTALLATION.md) for manual installation and update instructions.

## Setup

During setup, Home Assistant asks for:

| Field | Description |
| --- | --- |
| Host/IP address | Device hostname or local IP address |
| Port | Local API port, default `8080` |
| Local API Token / Wi-Fi Password | Local API token, or Wi-Fi password for current MVP firmware |

After setup, the integration creates one relay switch entity for each supported Load Box channel.

## Usage

- Use the created switch entities directly in dashboards, automations, scenes, and scripts.
- Rename relay channel entities in Home Assistant to match the connected loads.
- For lighting circuits, create a Home Assistant Switch as Light helper before exposing the entity to voice assistants.
- Expose only the entities you want Google Assistant or Alexa to control.
- Use the Identify button to locate a physical Smart Gate device when supported by firmware.

## Voice Assistants

Google Assistant and Amazon Alexa work through Home Assistant entity exposure.

For Home Assistant Cloud:

1. Open Settings > Voice assistants.
2. Select the Google Assistant or Alexa integration.
3. Open Expose.
4. Choose the Smart Gate entities you want to expose.

For lamps and lighting circuits, create a Home Assistant Switch as Light helper first, then expose the light entity instead of the raw switch. This gives voice assistants a more natural lighting model.

## Security

- The integration sends the configured token using:

  ```text
  Authorization: Bearer <token>
  ```

- The token is stored in Home Assistant config entry storage.
- Current firmware may use the device Wi-Fi password as a temporary Local API Token.
- Future firmware and app versions should use a dedicated local token.
- Do not expose the Smart Gate Local API port to the internet.

## Troubleshooting Summary

- Device unavailable: confirm power, Wi-Fi, IP address, port `8080`, and local network routing.
- Wrong token: update the Local API Token / Wi-Fi Password from the Smart Gate integration reauthentication flow or options.
- HACS update issue: reinstall or redownload Smart Gate from HACS, then restart Home Assistant.
- Logo/cache issue: restart Home Assistant and hard refresh the browser.
- Google/Alexa not seeing entities: confirm the entities are exposed in Home Assistant voice assistant settings.

See [Troubleshooting](docs/TROUBLESHOOTING.md) for detailed steps.

## Links

- [Installation Guide](docs/INSTALLATION.md)
- [Local API Guide](docs/LOCAL_API.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Brand Assets](docs/BRAND_ASSETS.md)

## License

MIT License. See [LICENSE](LICENSE).

