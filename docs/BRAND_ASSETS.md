# Brand Assets

Home Assistant 2026.3 and newer can load local brand images from a custom integration package.

Required files:

```text
custom_components/smart_gate/brand/icon.png
custom_components/smart_gate/brand/logo.png
custom_components/smart_gate/brand/dark_icon.png
custom_components/smart_gate/brand/dark_logo.png
```

High-density variants are also included:

```text
custom_components/smart_gate/brand/icon@2x.png
custom_components/smart_gate/brand/logo@2x.png
custom_components/smart_gate/brand/dark_icon@2x.png
custom_components/smart_gate/brand/dark_logo@2x.png
```

Guidelines:

- Use official Smart Gate brand assets only.
- Keep transparent backgrounds where possible.
- Use PNG files with exact filenames.
- Keep file sizes reasonable for Home Assistant UI loading.
- Do not source brand files from firmware.

## Home Assistant And HACS Notes

Home Assistant can display local custom integration brand files in Devices & Services on versions that support integration-local branding.

HACS dashboard icon display may depend on HACS cache and version behavior. It may not always reflect local brand assets immediately after a file update.

Troubleshooting:

1. Restart Home Assistant.
2. Clear browser cache or hard refresh.
3. Reload the Smart Gate integration.
4. Reinstall or update from HACS.
5. Verify `/custom_components/smart_gate/brand/icon.png` exists on the Home Assistant host.
