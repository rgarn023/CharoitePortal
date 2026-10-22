# Touhou Pocket Launcher — project handoff

Updated: October 22, 2026

## Workflow
- ChatGPT is sole developer and uses **connected GitHub tools**. Never suggest Cursor or another coding agent. Discover `mcp__GitHub__` actions via `functions.exec` / `ALL_TOOLS` before claiming unavailable.
- Repository: **https://github.com/rgarn023/TouhouPocketLauncher** (public, user-created). Work on existing `main` branch unless explicitly directed otherwise.
- User wants a handoff when chat becomes long; prepare a complete continuation summary at that point, including repo, branch, latest commit and CI/APK status.

## Requirements
- Free, standalone Android Touhou Pocket Launcher by Charoite Games; Galaxy S26 Ultra priority; mobile responsive.
- Import/install user-owned Touhou Windows EXEs with bundled licensed Wine/Box64 compatibility stack (no separate Winlator app), install independent English patches, no thcrap.
- Highest game priorities: Touhou Puppet Dance Performance base, Shard of Dreams, Shard of Dreams Extended, and their English translations. Later other Touhou games.
- Touch controls, Bluetooth controller, save backup/restore, reliable graphics/audio, and game-native speed are future milestones.

## Shard of Dreams `notkey` bug (important)
- Wine versions prior to 9.21 may incorrectly fail to resolve base-game installation with Japanese path. A documented workaround is a symlink exactly named `notkey` **inside the Shard of Dreams game directory**, pointing to the base TPDP folder.
- Steam Deck guide: https://gist.github.com/RobertTheSable/6c4d705623b4de8d8cb3c954eac4814f
- Wine bug report: https://bugs.winehq.org/show_bug.cgi?id=54295
- Wine 9.21+ reportedly fixes it. Only enable workaround if game/runtime test actually requires it.
- Pure Kotlin helper `NotkeyLinkManager.kt` with JVM tests exists. Its creation method must only be invoked after a private Wine prefix and the two game installation folders exist. **It has NOT been integrated into a working Wine runtime yet.**

## Implemented so far
- Android Kotlin Activity UI, SAF game folder import, TPDP/Shards/Extended candidate recognition.
- EXE staging and ZIP safety inspection/staging (NOT execution or patch application).
- GitHub Actions Android debug APK workflow, JUnit tests for recognition/archive inspection and `notkey` symlink behavior.
- Source is being committed through connected GitHub tools, on `main`. Confirm the latest branch and Action build status.

## Not done
- Wine/Box64 runtime, graphics drivers, game launch, actual patch applying, install orchestration, DXGI override for Extended, gamepad, full device validation, performance benchmarks.
- No copyrighted game files or patches bundled, never claim working gameplay before tested.

## Immediate next steps
1. Check workflow run(s) and fix first Android build errors.
2. Build and verify debug APK; user can test import UI on Galaxy.
3. Examine upstream Winlator code and individual license obligations. Implement runtime integration rather than repackaging a proprietary APK.
4. Add installer flow base TPDP > SoD > English patch > Extended, conditional `notkey` compatibility and `dxgi` override, with rollback.
5. Validate on phone with user-owned game assets.
