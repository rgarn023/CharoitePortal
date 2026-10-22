# Touhou Pocket Launcher

Independent experimental Android launcher for **user-owned** Windows Touhou games by Charoite Games. Top priorities: **Touhou Puppet Dance Performance**, **Shard of Dreams** and **Shard of Dreams Extended**, with **standalone English patches** (not thcrap).

## Current builds (October 22, 2026)

| Variant | Purpose | Status |
| --- | --- | --- |
| **Native starter alpha** | Import game folders, recognize titles and stage EXE/ZIP inputs | GitHub build + unit tests passed; no Windows execution |
| **Integrated Wine runtime preview** | Standalone Wine/Box64 runtime and graphics environment with a Touhou entry screen | GitHub build passed; phone installation and gameplay **not tested** |

**[Runtime preview APK, GitHub Actions run #39787333874](https://github.com/rgarn023/TouhouPocketLauncher/actions/runs/39787333874)** — open **Artifacts** and download `touhou-pocket-runtime-preview-apk`, then extract `app-debug.apk`.

The runtime preview comes from a **pinned upstream [Winlator-app](https://github.com/brunodev85/winlator-app)** source revision with a small public overlay and upstream licensing notices. It does **not** require the separate Winlator app, but it currently opens the original Wine/Box64 container interface. It has **not** yet gained automated game installation, patching, or one-tap TPDP launch.

The upstream-compatible runtime APK is approximately 158 MB before installation and will need additional free storage to unpack Wine and user-supplied games. You may keep the native alpha installed alongside the runtime preview; they have different Android application IDs.

## Start testing the runtime on Android
1. Download the runtime preview Actions artifact; extract and install `app-debug.apk`.
2. Open Touhou Pocket Launcher > **Open Windows Runtime**.
3. Confirm Winlator's first-run runtime installation completes, and create an isolated container.
4. Import **your legally obtained TPDP base-game files** into a location visible to the Windows container, and test the unpatched base game before the expansion.
5. Record whether the installer/game launches, rendering quality, controls, audio, errors, and screenshots. Do **not** assume English patches or Shard of Dreams Extended work yet.

See [runtime testing guide](docs/RUNTIME-TEST.md) and [handoff](docs/HANDOFF.md).

## Features planned
- Library and game/expansion version recognition with SAF integration.
- Automated Windows game installer and portable game import into an isolated prefix.
- Safe offline English patch installation with hashing, backups, and rollback (**no thcrap**).
- TPDP base > Shard of Dreams > English translation > optional Extended; conditional `notkey` compatibility and `dxgi.dll` handling.
- Mobile touch controls, gamepad, saves, responsive UI, native-rate graphics/audio tuning.

**No copyrighted Touhou game data, expansions, or translations are included.** Runtime redistributions must comply with Winlator LGPL-2.1 and the licenses of Wine/Box64/graphics components; upstream attributions are included with the runtime preview and in [runtime-preview/NOTICE.md](runtime-preview/NOTICE.md).
