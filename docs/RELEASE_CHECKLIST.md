# Release Checklist

## Pre-release

- Fresh clone test completed.
- `python -m compileall custom_components/smart_gate` passes.
- JSON validation passes for `hacs.json`, manifest, translations, and `strings.json`.
- HACS custom repository install tested.
- Hassfest run locally or tracked as a release follow-up.
- Clean Home Assistant install tested.
- Auto-discovery tested.
- Manual setup tested.
- Wrong IP friendly error tested.
- Duplicate setup friendly error tested.
- Already-in-progress friendly error tested.
- Device unavailable/recovery tested.
- Compatible SG-Load-Box firmware with Local API v1 diagnostics tested.
- No new Home Assistant tracebacks.
- Screenshots updated if screenshots are included.
- Changelog updated.

## GitHub

- Repository is public.
- Repository description is added.
- Repository topics are added:
  - `home-assistant`
  - `home-assistant-custom-component`
  - `hacs`
  - `smart-home`
  - `iot`
  - `smart-gate`
  - `local-control`
- Release tag is `v0.4.0`.
- Full GitHub Release is created, not only a tag.

## HACS

- `hacs.json` is valid.
- Repository contains exactly one integration under `custom_components`.
- Manifest has `documentation`, `issue_tracker`, `codeowners`, `name`, and `version`.
- HACS Action can be added later if it is confirmed reliable for this repository.

## Runtime UX Acceptance

- New HA install plus HACS install succeeds.
- Auto-discovery card appears.
- Discovery confirmation text uses the friendly Smart Gate name.
- Device is created with area selection.
- SW1-SW6 appear for tested `IO_PROFILE_6`.
- Identify button works.
- Diagnostic sensors and binary sensors appear.
- Wrong IP shows friendly `cannot_connect`.
- Duplicate setup shows friendly `already_configured`.
- Already open flow shows friendly `already_in_progress`.
- Offline/recovery works.
- Boot physical state wins with compatible firmware.
- No HA traceback appears in logs.
