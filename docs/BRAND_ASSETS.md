# Brand Assets

Home Assistant custom integrations can load local brand images from the integration package.

Required files:

```text
custom_components/smart_gate/brand/icon.png
custom_components/smart_gate/brand/logo.png
custom_components/smart_gate/brand/dark_icon.png
custom_components/smart_gate/brand/dark_logo.png
```

Recommended sizes:

- `icon.png`: square, 256x256 or 512x512.
- `dark_icon.png`: square, dark-mode optimized.
- `logo.png`: wider logo, 512x128 or similar.
- `dark_logo.png`: wider dark-mode optimized logo.

Guidelines:

- Use official Smart Gate brand assets only.
- Keep transparent backgrounds where possible.
- Use PNG files with exact filenames.
- Keep file sizes small enough for Home Assistant UI loading.
- Restart Home Assistant and hard refresh the browser after changing brand assets.

Home Assistant 2026.3 and newer can use these local custom integration brand files.
