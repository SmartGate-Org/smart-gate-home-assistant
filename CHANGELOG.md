# Changelog

## 0.4.0

- Prepared the Smart Gate Home Assistant integration for public HACS release.
- Added release documentation, install guide, troubleshooting guide, Local API docs, product support notes, and release checklist.
- Added GitHub validation workflow, issue templates, and pull request template.
- Confirmed source-based HACS packaging with one integration under `custom_components/smart_gate`.
- Kept SG-Load-Box support, existing switch unique IDs, Zeroconf discovery, manual setup, diagnostics, and Options Flow unchanged.
- Documented compatible firmware behavior for boot physical-state protection and Local API v1 diagnostics.

Known limitations:

- SG-Load-Box is the only officially supported product in v0.4.0.
- Local HTTP auth is not implemented yet unless supported by future firmware.
- Smart Gate is not yet submitted as an official Home Assistant Core integration.

## 0.3.0

- Added boot physical-input authority so MCP/manual startup state wins over stale cloud retained state.
- Added startup cloud publish guard and stale WSS switch-state ignore window while preserving `doUpdateNow=true`.
- Added firmware Local API diagnostics for Wi-Fi RSSI, IP address, WSS status, startup sync flags, and last command/source timestamps.
- Added Home Assistant diagnostic sensors and binary sensors for Wi-Fi RSSI, IP address, Cloud connection, Local API, last command source, and last seen.
- Added firmware identity helpers for `Smart-Gate-<short_product_id>` default naming.
- Added `/v1/info` name fields: `short_id`, `friendly_name`, and `hostname`.
- Added local rename endpoint `POST /v1/config/name`.
- Updated mDNS instance and TXT records to publish Smart Gate friendly/network metadata.
- Added Home Assistant Options Flow for device name and polling interval.
- Added firmware friendly-name sync into Home Assistant defaults while respecting HA user renames.
- Changed default relay labels to `SW1`, `SW2`, and so on while preserving switch unique IDs.
- Added profile/channel-count-aware reload handling.
- Updated onboarding, troubleshooting, and Local API documentation.

## 0.2.0

- Productized the Smart Gate Home Assistant custom integration for HACS packaging.
- Added English and Arabic custom integration translations.
- Added friendly SG-Load-Box device naming.
- Added Identify button entity.
- Added diagnostic sensors for uptime, free heap, firmware version, and API version.
- Added HACS metadata and end-user documentation.

## 0.1.0

- Initial local-only SG-Load-Box integration.
- Added Zeroconf discovery, manual config flow, `/v1/state` polling, and one switch entity per relay channel.
