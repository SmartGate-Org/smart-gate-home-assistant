# Smart Gate

Home Assistant custom integration package files for Smart Gate devices.

Use the repository root README and docs for installation, local auth, and release notes:

- `README.md`
- `docs/INSTALLATION.md`
- `docs/TROUBLESHOOTING.md`
- `docs/LOCAL_API.md`
- `docs/BRAND_ASSETS.md`

Supported in v0.5.0:

- SG-Load-Box local HTTP control.
- Local API Token / Wi-Fi Password setup support.
- Auth-required Zeroconf confirmation flow.
- Reauth flow for firmware `401 Unauthorized` responses.
- Options Flow for host, port, token, device name, and polling interval.
- Zeroconf discovery.
- Channel 1..N switch entities with stable unique IDs.
- Identify button.
- Diagnostic sensors and binary sensors.
