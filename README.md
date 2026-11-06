# Starproof for Wedgie

The installable hardware signer for [Starproof](https://starproof-wedgie.vercel.app), a space exploration game. Launch, travel, collect artifacts and refuel using a manufacturer-certified OPTIGA Trust M key. Browser game: [NikolaiL/starproof](https://github.com/NikolaiL/starproof). Shared toolkit: [wedgie-actions](https://github.com/NikolaiL/wedgie-actions).

## Install through wedgie.dev

1. Connect your Wedgie in desktop Chrome or Edge at [wedgie.dev/connect](https://wedgie.dev/connect).
2. Open **Apps from a GitHub repo** and add **`NikolaiL/wedgie-starproof`**.
3. Select **Starproof**, review the source, then press the physical green button to install.
4. Close that connection and open [Starproof](https://starproof-wedgie.vercel.app).

Requires firmware **0.3.76+**, a 240×240 display and an **OPTIGA Trust M** chip. This is a community app, not a reviewed Wedgie shelf app. Installation selects Starproof as the running app and requires full-control approval on the device. Review [wedgie.json](wedgie.json) and [device/](device/) before installing.

For CLI installation, clone this repository and run `python3 /path/to/wedgie.py install .`. Obtain the official CLI from [wedgie.dev](https://wedgie.dev/wedgie.py); it needs `pyserial`.

## Controls and screens

- **Green:** approve the displayed action. **Red:** decline.
- Travel previews show the destination planet, source and fuel cost.
- Artifact previews show the relic, credits and map rewards.
- Refills show a free cache or the exact credit price.
- Cancelling in the browser dismisses the device prompt without signing.

Only real physical presses can approve; USB can cancel but cannot approve. The app reads the existing factory certificate and signs with the existing factory key. It creates/replaces/locks no keys and does not write Safe Signer's key slots. It accepts only Starproof's pinned production origin or localhost demo ports. This proves chip participation, not firmware attestation or human presence.

## Develop

`npm ci && npm test` checks Python parsing, physical-only cancellation, artwork bounds and vendored helper provenance. Node 24+ and Python 3 are required on the development computer; the installed app uses MicroPython. Run `npm run sync:device` after deliberately upgrading `wedgie-actions`. Artwork is procedural and needs no extra device assets.

MIT. Built with AI assistance during ETHGlobal Mumbai Classic, November 6, 2026. Wedgie firmware supplies `ui`, `lcd`, `wedgie` and `optiga`; the common helper is vendored from `wedgie-actions`.
