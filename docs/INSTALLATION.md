# Installation

## HACS Installation

Use this flow for a new Home Assistant machine:

1. Install HACS if it is not already installed.
2. Open HACS > Integrations.
3. Open the three-dot menu and choose Custom repositories.
4. Add:

   ```text
   https://github.com/SmartGate-Org/smart-gate-home-assistant
   ```

5. Set Category to Integration.
6. Download Smart Gate.
7. Restart Home Assistant.
8. Power on the Smart Gate device.
9. Add the device to Wi-Fi using the Smart Gate app or supported BLE provisioning.
10. Confirm Home Assistant and the Smart Gate device are on the same LAN/VLAN.
11. Open Settings > Devices & services.
12. Smart Gate should appear under Discovered.
13. Click Add.
14. Select an Area if desired.
15. Finish setup.

If the integration does not appear after install, hard refresh your browser and restart Home Assistant once more.

## Manual Fallback

If discovery is unavailable, add Smart Gate manually:

1. Open Settings > Devices & services.
2. Click Add Integration.
3. Search for Smart Gate.
4. Enter Host:

   ```text
   Smart-Gate-xxxx.local
   ```

   or the device IP address.

5. Enter Port:

   ```text
   8080
   ```

The integration validates the device with `GET /v1/info` and uses the firmware `device_id` as the stable unique ID.

## Manual File Installation

Copy this folder:

```text
custom_components/smart_gate
```

to your Home Assistant configuration directory:

```text
/homeassistant/custom_components/smart_gate/
```

Common Home Assistant OS host path:

```text
/mnt/data/supervisor/homeassistant/custom_components/smart_gate/
```

Restart Home Assistant after copying or updating the files.

## First Setup Checklist

1. Confirm the device Local API is enabled.
2. Confirm `http://DEVICE_IP:8080/v1/info` returns JSON.
3. Confirm mDNS is available for discovery, or use manual setup.
4. Press Identify after setup to locate the physical device.
5. Rename the physical/network device from Smart Gate Options if needed.
6. Rename channel entities in Home Assistant if desired.
