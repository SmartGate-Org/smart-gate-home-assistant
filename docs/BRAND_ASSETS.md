# Brand Assets

This repository includes Smart Gate brand files for GitHub, HACS, and Home Assistant.

## Repository Brand Files

| File | Use |
| --- | --- |
| `brand/icon.png` | Repository and HACS icon |
| `brand/logo.png` | Repository README logo |

## Integration Brand Files

| File | Use |
| --- | --- |
| `custom_components/smart_gate/brand/icon.png` | Home Assistant integration icon |
| `custom_components/smart_gate/brand/logo.png` | Home Assistant integration logo |

Dark and high-density variants are also included for supported Home Assistant views.

## Cache Behavior

Home Assistant and HACS may cache logos and icons after installation or update.

If the logo does not update:

1. Restart Home Assistant.
2. Hard refresh the browser.
3. Clear browser cache.
4. Redownload Smart Gate from HACS if needed.

The integration package should keep the brand filenames unchanged so Home Assistant and HACS can find them consistently.
