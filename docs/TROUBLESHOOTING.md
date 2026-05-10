# Troubleshooting

Use this guide to resolve common Smart Gate Home Assistant integration issues.

## Device Unavailable After Reboot

During a Smart Gate device reboot, Home Assistant entities may become unavailable. They should recover automatically when the Local API is available again.

If the device stays unavailable:

1. Confirm the device is powered on.
2. Confirm the device is connected to Wi-Fi.
3. Confirm Home Assistant and the device are on the same local network.
4. Open this URL from a browser on the same network:

   ```text
   http://<DEVICE_IP>:8080/v1/info
   ```

5. Reload the integration from Settings > Devices & services > Smart Gate.
6. Restart Home Assistant if the integration still does not reconnect.

## Wrong Token Or Invalid Auth

If setup or reauthentication shows `invalid_auth`, the device rejected the Local API Token.

For current MVP firmware, enter the device Wi-Fi password in the field labeled:

```text
Local API Token / Wi-Fi Password
```

To update the token:

1. Open Settings > Devices & services.
2. Select Smart Gate.
3. Complete the reauthentication prompt, or open Configure/Options if available.
4. Enter the current Local API Token / Wi-Fi Password.

Do not share real tokens or Wi-Fi passwords in support screenshots or logs.

## No Entities Created

Check the following:

- The device is a supported Smart Gate product.
- Local API is enabled on the device firmware.
- Home Assistant can reach the device on port `8080`.
- The setup form was completed successfully.
- Home Assistant was restarted after installing the custom integration.

If entities still do not appear, reload the integration from Settings > Devices & services.

## Device IP Changed

The integration can update the stored host and port when Zeroconf discovers the same Smart Gate device at a new address.

If the integration does not reconnect:

1. Confirm the device is online at the new IP address.
2. Confirm mDNS/Zeroconf is working on your network.
3. Reload the Smart Gate integration.
4. If mDNS is unavailable, open the integration options and enter the new host/IP address manually.

The stored Local API Token is kept when the host or port changes.

## HACS Update Fails

Try these steps:

1. Open HACS > Integrations > Smart Gate.
2. Select Redownload or Update.
3. Restart Home Assistant.
4. Confirm the folder exists:

   ```text
   custom_components/smart_gate
   ```

5. If needed, remove the integration files and install again through HACS.

Do not delete the Smart Gate device entry unless you want to set it up again.

## Logo Not Showing In HACS Or Home Assistant

Home Assistant and HACS may cache images.

Try:

1. Restart Home Assistant.
2. Hard refresh the browser.
3. Clear browser cache.
4. Redownload Smart Gate from HACS.
5. Confirm these files exist:

   ```text
   custom_components/smart_gate/brand/icon.png
   custom_components/smart_gate/brand/logo.png
   ```

## Google Or Alexa Does Not See Devices

Google Assistant and Amazon Alexa use Home Assistant entity exposure.

For Home Assistant Cloud:

1. Open Settings > Voice assistants.
2. Select Google Assistant or Alexa.
3. Open Expose.
4. Enable the Smart Gate entities you want to control.
5. Ask Google or Alexa to sync devices if needed.

For lighting circuits, create a Home Assistant Switch as Light helper and expose the light helper instead of the raw switch.

## Google Or Alexa Only Controls One Light

If a voice command controls only one channel:

- Confirm each intended channel is exposed to the voice assistant.
- Use clear, unique names for each exposed entity.
- Use Home Assistant groups or areas for room-level commands.
- For lights, expose Switch as Light helpers instead of raw switch entities.
- Confirm the Smart Gate integration is updated to the latest version.

## Restart Or Reload Instructions

Reload the integration:

1. Open Settings > Devices & services.
2. Select Smart Gate.
3. Open the three-dot menu.
4. Select Reload.

Restart Home Assistant:

1. Open Settings > System.
2. Select Restart Home Assistant.
3. Wait for Home Assistant to come back online.

## Local API Checks

Public check:

```bash
curl http://<DEVICE_IP>:8080/v1/info
```

Protected check:

```bash
curl -H "Authorization: Bearer <LOCAL_API_TOKEN>" http://<DEVICE_IP>:8080/v1/state
```
