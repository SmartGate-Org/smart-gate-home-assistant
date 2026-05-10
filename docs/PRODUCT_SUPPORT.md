# Product Support

Smart Gate for Home Assistant currently supports Smart Gate Load Box devices with the local HTTP API enabled.

## Compatibility

| Product | Status |
| --- | --- |
| SG-Load-Box | Supported |
| SG-MiniBox | Planned |
| SG-Touch-Box | Planned |
| SG-Presence-Radar | Planned |
| SG-Temp-Hum | Planned |

## SG-Load-Box

The integration creates one switch entity for each relay channel reported by the device. Channel entities can be renamed in Home Assistant to match the connected load, room, or circuit.

For lighting circuits, use the Home Assistant Switch as Light helper before exposing the entity to Google Assistant or Amazon Alexa.

## Firmware Requirements

The device firmware should provide:

- Local HTTP API
- Zeroconf/mDNS discovery
- Stable device identity
- Relay state reporting
- Local relay control

For setup requirements, see the [Installation Guide](INSTALLATION.md).
