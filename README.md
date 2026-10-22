# Touhou Pocket Launcher

An experimental Charoite Games Android launcher for user-owned Windows Touhou games, initially **Touhou Puppet Dance Performance**, **Shard of Dreams**, and **Shard of Dreams Extended**.

**Status: Android UI and file-import prototype; not a game emulator yet.** The APK cannot install or run Windows executables until a properly licensed Wine/Box64-based runtime is integrated and verified on actual Android hardware.

## First milestone
- Native Android game library and secure Storage Access Framework folder import.
- Detect candidate TPDP, Shard of Dreams, Extended, and numbered Touhou executables.
- Stage EXE installers and inspect/stage ZIP patches. No execution or patch application yet.
- Build an installable *development* APK using GitHub Actions.
- Prepare automatic Shard of Dreams `notkey` symlink workaround when a private Wine prefix is available.

## Roadmap
1. Verify APK import UI on Galaxy S26 Ultra.
2. Integrate legally redistributable Wine/Box64/graphics components, honoring each upstream license.
3. Implement isolated EXE installation and execution and game-specific compatibility profiles.
4. Support independently applicable English patches (**no thcrap**), version/hash validation, backups and restore.
5. Support base TPDP, Shard of Dreams (`notkey` compatibility), Extended (including DLL override).
6. Optimize touch, gamepad, full-speed frame pacing, audio, and stability.

Users must supply their legally obtained Windows games and patches. This repo distributes no commercial game data.

For ongoing project state, see [docs/HANDOFF.md](docs/HANDOFF.md).
