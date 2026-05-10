# Installation Guide

This guide explains how to install and set up the Smart Gate Home Assistant integration.

## Requirements

- Home Assistant 2026.4.0 or newer
- HACS 2.0.0 or newer
- Smart Gate device connected to the same local network as Home Assistant
- Local API enabled on the device firmware
- Local API token, or Wi-Fi password for current MVP firmware

## Install With HACS

1. Open Home Assistant.
2. Open HACS.
3. Go to Integrations.
4. Open the three-dot menu and select Custom repositories.
5. Add:

   ```text
   https://github.com/SmartGate-Org/smart-gate-home-assistant
   ```

6. Set Category to Integration.
7. Select Add.
8. Search for Smart Gate in HACS.
9. Download the Smart Gate integration.
10. Restart Home Assistant.

## Add The Integration

1. Open Settings > Devices & services.
2. If Smart Gate appears under Discovered, select Add.
3. If it does not appear, select Add Integration and search for Smart Gate.
4. Enter the setup fields:

   | Field | Description |
   | --- | --- |
   | Host/IP address | Device hostname or local IP address |
   | Port | Local API port, default `8080` |
   | Local API Token / Wi-Fi Password | Local API token, or Wi-Fi password for current MVP firmware |

5. Select an area if desired.
6. Finish setup.

The integration creates relay switch entities for supported Smart Gate Load Box channels.

## Manual Installation

Use manual installation only if HACS is not available.

1. Download this repository.
2. Copy this folder:

   ```text
   custom_components/smart_gate
   ```

3. Place it in your Home Assistant configuration directory:

   ```text
   /homeassistant/custom_components/smart_gate/
   ```

4. Restart Home Assistant.
5. Open Settings > Devices & services.
6. Select Add Integration and search for Smart Gate.

## Updating

To update through HACS:

1. Open HACS > Integrations.
2. Open Smart Gate.
3. Select Update or Redownload.
4. Restart Home Assistant after the update completes.

If the integration does not appear after updating, refresh the browser and restart Home Assistant once more.
