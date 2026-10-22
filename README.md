# Touhou Pocket Launcher

Touhou Pocket Launcher is an experimental **standalone Android launcher** by Charoite Games for user-owned Windows Touhou games. The first compatibility targets are **Touhou Puppet Dance Performance**, **Shard of Dreams**, and **Shard of Dreams Extended**. Independent English patch support is planned; **thcrap is not part of the design**.

## Builds

- **Touhou-integrated runtime APK** — a dedicated Android Touhou library screen, automatic private Wine/Box64 setup, imported game-folder and EXE support, installed-game scan, and direct Play actions. Does **not** show Winlator's container-manager interface. Its in-game renderer still derives from Winlator. **Phone/game compatibility remains unverified.**
- **Earlier Kotlin import-only alpha** — separate smaller APK without Windows execution, retained for testing and reference.

The integrated APK is built by [Touhou Wine Runtime Preview](https://github.com/rgarn023/TouhouPocketLauncher/actions/workflows/runtime-preview.yml) in GitHub Actions. Select the latest **successful** workflow run, download the `touhou-pocket-runtime-preview-apk` artifact, and extract `app-debug.apk`.

## First-time Android testing

1. Install the **new** runtime APK (not the previous runtime preview which still opened Winlator's container manager).
2. Open Touhou Pocket Launcher and tap **Set Up Game Engine**. Allow extraction and game-environment creation to complete (requires free storage).
3. Choose **Import Game Folder** and select a complete, legally obtained portable TPDP game folder. The files are copied into an isolated Windows C: drive owned by the app.
4. Tap **Play** in the Touhou library. The selected executable is launched directly through Wine without navigating a container manager.
5. If you have a Windows **installer EXE** instead, choose **Import Windows Game Installer**, tap **Run Installer**, complete its prompts, then tap **Find Installed Touhou Games** to index recognized game executables.

**Do not test Shard of Dreams, Extended, or patches before the base game is working.** Installer compatibility, graphics, audio, and performance all require real-device validation. English patch application, `notkey` automation, backup/restore, and custom touch controls are not implemented in this build.

See [Android testing guide](docs/RUNTIME-TEST.md) and [project handoff](docs/HANDOFF.md).

## How it works

The APK builds from pinned, openly licensed [Winlator Android source](https://github.com/brunodev85/winlator-app) and uses its Wine/Box64 display/backend, but replaces the app's initial entry screen and hides the original container-manager launcher from users. There is **no requirement to install Winlator as a separate app**.

The development overlay is in [runtime-preview](runtime-preview/). Upstream LGPL-2.1 and additional third-party license notices must be preserved. No proprietary games, expansions, or English translations are distributed.
