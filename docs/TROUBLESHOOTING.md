# Troubleshooting

## Smart Gate Not Discovered

- Confirm the device is powered on.
- Confirm the device is connected to Wi-Fi.
- Confirm Home Assistant and the device are on the same LAN/VLAN.
- Confirm TCP port `8080` is reachable.
- Confirm firmware has `local_http` and mDNS enabled.
- If mDNS does not cross VLANs, use manual setup.

mDNS service:

```text
_smartgate._tcp.local.
```

Useful checks:

```text
dns-sd -B _smartgate._tcp
dns-sd -L Smart-Gate-xxxx _smartgate._tcp local
```

## Manual Setup Cannot Connect

Test the public Local API from a machine on the same network:

```powershell
Invoke-RestMethod http://DEVICE_IP:8080/v1/info
Invoke-RestMethod http://DEVICE_IP:8080/v1/health
```

If these fail, check the IP address, firewall rules, VLAN routing, and whether the device is still connected to Wi-Fi.

## Invalid Local API Token

If setup or runtime reauth shows `invalid_auth`, firmware rejected a protected Local API request with HTTP `401`.

For current MVP firmware, enter the device Wi-Fi password in the field labeled:

```text
Local API Token / Wi-Fi Password
```

Later firmware may use an app-generated local token instead.

PowerShell test with a token variable:

```powershell
$headers = @{ Authorization = "Bearer <token>" }
Invoke-RestMethod -Uri "http://DEVICE_IP:8080/v1/state" -Headers $headers
```

Curl test:

```bash
curl -H "Authorization: Bearer <token>" http://DEVICE_IP:8080/v1/state
```

Do not paste real Wi-Fi passwords or tokens into screenshots, issue reports, public logs, or shared support chats.

## Reauth Prompt Appears

Home Assistant starts a reauth flow when firmware returns `401 Unauthorized` after setup.

Use Settings > Devices & services > Smart Gate and enter the current Local API Token / Wi-Fi Password. You do not need to delete and re-add the integration.

## Already Configured

Smart Gate uses the firmware `device_id` as the Home Assistant unique ID. If Home Assistant says the device is already configured, use the existing Smart Gate entry instead of adding it again.

## Already In Progress

Another setup flow for the same Smart Gate device is already open. Finish or close the existing setup flow before starting another one.

## Device Unavailable

- The device may be rebooting.
- Wi-Fi may be disconnected.
- The Local API may be unreachable.
- Home Assistant may not be able to route to the device network.
- If auth was recently enabled, the stored token may need reauth.

The Local API diagnostic is on only when Home Assistant can poll the device successfully.

## Cloud Disconnected But Local API Connected

Home Assistant local control can still work when Cloud connection is off. Cloud connection reflects the firmware WSS/cloud state, not whether Home Assistant can control the relays locally.

## Local API Disconnected

If Local API is disconnected, Home Assistant cannot reach the device locally. Check power, Wi-Fi, IP address, VLAN routing, port `8080`, and token validity.

## Low Wi-Fi RSSI

Wi-Fi RSSI is reported in dBm. Values closer to `0` are stronger. If RSSI is very low, move the device or access point, reduce obstacles, or improve 2.4 GHz coverage.

## Channels Missing After Profile Change

The integration trusts firmware `/v1/info` and `/v1/state` for channel count. If a Load Box profile changes:

1. Reload the Smart Gate integration.
2. Restart Home Assistant if entities do not refresh.
3. Remove and re-add the integration only if stale entities remain confusing.

Home Assistant may keep old entity registry entries rather than deleting them automatically.

## Name Does Not Update

- Device identity is still `device_id`; friendly name is display metadata.
- Firmware must expose `friendly_name` or `hostname` in `/v1/info`.
- Home Assistant will not overwrite a device name changed manually in the HA UI.
- To update the physical/network name from HA, use Smart Gate integration Options > Device name.

## Hostname Does Not Appear In Router

Some routers cache DHCP hostnames until lease renewal. mDNS may update faster than the router UI.

Try reconnecting Wi-Fi, rebooting the device, or waiting for DHCP lease renewal.

## Logo Or Icon Not Showing

Home Assistant 2026.3 and newer can load local brand files from `custom_components/smart_gate/brand/`.

Troubleshooting steps:

- Confirm `custom_components/smart_gate/brand/icon.png` exists.
- Confirm `logo.png`, `dark_icon.png`, and `dark_logo.png` exist.
- Restart Home Assistant.
- Clear browser cache or hard refresh the browser.
- Reload the Smart Gate integration.
- Reinstall or update from HACS if files are stale.

HACS dashboard icon display may depend on HACS cache/version behavior and may not immediately reflect local brand assets.

## API Tests

Public:

```powershell
Invoke-RestMethod http://DEVICE_IP:8080/v1/info
Invoke-RestMethod http://DEVICE_IP:8080/v1/health
```

Protected:

```powershell
$headers = @{ Authorization = "Bearer <token>" }
Invoke-RestMethod http://DEVICE_IP:8080/v1/state -Headers $headers
Invoke-RestMethod -Method Post -Uri http://DEVICE_IP:8080/v1/control -Headers $headers -ContentType "application/json" -Body '{"request_id":"ha-test","relays":"1-0-0-0-0-0"}'
Invoke-RestMethod -Method Post -Uri http://DEVICE_IP:8080/v1/identify -Headers $headers
Invoke-RestMethod -Method Post -Uri http://DEVICE_IP:8080/v1/config/name -Headers $headers -ContentType "application/json" -Body '{"request_id":"ha-name-test","friendly_name":"Smart-Gate-Test"}'
```

```bash
curl http://DEVICE_IP:8080/v1/info
curl http://DEVICE_IP:8080/v1/health
curl -H "Authorization: Bearer <token>" http://DEVICE_IP:8080/v1/state
curl -X POST http://DEVICE_IP:8080/v1/identify -H "Authorization: Bearer <token>"
curl -X POST http://DEVICE_IP:8080/v1/control -H "Authorization: Bearer <token>" -H "Content-Type: application/json" -d '{"request_id":"ha-test","relays":"1-0-0-0-0-0"}'
curl -X POST http://DEVICE_IP:8080/v1/config/name -H "Authorization: Bearer <token>" -H "Content-Type: application/json" -d '{"request_id":"ha-name-test","friendly_name":"Smart-Gate-Test"}'
```

## Logs

Home Assistant OS:

```text
ha core logs -f | grep -i "smart_gate\|custom_components.smart_gate\|traceback\|error"
```

Home Assistant UI:

```text
Settings > System > Logs
```
