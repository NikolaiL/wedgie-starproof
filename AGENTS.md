# Repository Guidelines

## Structure

This repository contains the installable Starproof Wedgie app. `wedgie.json` is the installation manifest; `device/` contains its five MicroPython modules. Files flatten onto device flash, so preserve the `starproof` prefix. `starproof_actions.py` is vendored from `wedgie-actions`; `tools/sync-device.js` updates it. The browser game and server live in the separate `NikolaiL/starproof` repository.

## Development and Tests

Use Node.js 24+ and Python 3 for host checks: `npm ci`, then `npm test`. Run `npm run sync:device` after deliberately updating the pinned toolkit. Tests exercise cancellation, the strict signed action format, and artwork bounds. Test RAM and real display behavior on a physical Wedgie before releasing device changes; host tests cannot establish hardware behavior.

## Style and Compatibility

Use MicroPython-compatible Python, four spaces and snake_case. Keep allocations small on RP2040. Use firmware `ui.ask`, palette constants and physical-only keys for confirmation. Draw game previews only inside the existing content area; never obscure the firmware's title or answer bars. Poll USB cooperatively so cancellation stays responsive. Preserve the 600 ms settle behavior implemented by firmware.

## Security and Contributions

Derive labels and prices from validated signed fields. Never accept host-provided display labels as authority. A cancellation must match the pending request ID and produce no signature. Never create, replace or lock keys without explicit user instruction. Never inject a green press or use virtual wallets for real funds.

Use concise imperative commit subjects. Describe firmware requirements, validation, and screenshots in PRs. Preserve Classic provenance and disclose reused code and AI assistance. Coordinate protocol changes with the browser game's pinned device dependency; bump `appVersion` for releases so its installer can detect outdated apps.

Use AgentMemory when available: recall relevant context before substantial work, save durable decisions and lessons, and consolidate after substantial work. Never store secrets.
