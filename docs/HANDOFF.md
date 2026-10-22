# Touhou Pocket Launcher — project handoff

Updated: October 22, 2026. Use the latest GitHub commit as authoritative source.

## Development responsibility and workflow
- **ChatGPT is the sole developer** and makes changes directly with the connected GitHub tools. Do **not** tell user to use Cursor/Gemini or ask them to upload GitHub files. Discover `mcp__GitHub__` via `functions.exec` / `ALL_TOOLS` first if needed.
- Repository: https://github.com/rgarn023/TouhouPocketLauncher (public), default/current development branch **main**. Continue on main unless user explicitly asks otherwise.
- GitHub Actions compiles APKs. User only tests device functionality when that cannot be confirmed via CI.
- If chat becomes unwieldy, provide comprehensive handoff with source URLs, build status, next tasks, and user requirements. Latest main README and this file have the durable record.

## Requirements
- Free Android Touhou Pocket Launcher by Charoite Games, phone-first Galaxy S26 Ultra.
- **Completely standalone APK** with bundled license-compliant Wine/Box64 graphics runtime, no separate Winlator requirement.
- Support legally obtained Touhou Windows EXE installers / game folders; initially **Touhou Puppet Dance Performance** (TPDP), **Shard of Dreams** (SoD), **Shard of Dreams Extended** (Extended).
- Support independent English patches (ZIP or Windows installers when safe), with version checks and backups; **no thcrap**.
- Native mobile UX, touch controls and controllers, reliable saves, performance/graphics/audio.
- Do not bundle copyrighted Touhou games or patch content.

## Current source projects
**Native alpha**
- `app/src/main/java/games/charoite/touhoupocket/`: Kotlin UI, SAF folder import, game recognition, ZIP inspection, EXE/ZIP staging, local library.
- `NotkeyLinkManager.kt`: small safety checked symlink helper, covered by JVM tests. Not yet wired into a functional Windows install.
- `.github/workflows/android-debug.yml` builds alpha APK. Earlier successful run `39778165113`.
- Native alpha does **NOT** launch or install EXEs.

**Integrated Windows runtime preview (NEW, working GitHub build)**
- `runtime-preview/overlay.py`, `TouhouEntryActivity.java`, `NOTICE.md`, `.github/workflows/runtime-preview.yml`.
- Builds from pinned LGPL source of `brunodev85/winlator-app`, Git SHA `8077f374ef2d54127b088de9e8cd7b4af14d9c8b`. Uses rootfs, Wine, Box64, graphics assets and source-built Android/native components.
- Overlay modifies app label, appId to `games.charoite.touhoupocket.runtime`, FileProvider authority, entry launcher, embeds LGPL notices, leaves Winlator engine and container UI.
- **Build SUCCESS**: Actions run https://github.com/rgarn023/TouhouPocketLauncher/actions/runs/39787333874 (2026-10-22), artifact `touhou-pocket-runtime-preview-apk`, ~157 MB ZIP containing `app-debug.apk` (~157,563,163 bytes). APK ZIP integrity verified in development session, contains arm64 libraries, rootfs and LGPL notice.
- This **is not yet a complete dedicated game launcher**: entry page leads to original Winlator container UI, which can be used to test Windows game execution. **No Android device/TPDP gameplay verification has occurred.** Do not misrepresent build success as game compatibility.
- License: see `runtime-preview/NOTICE.md`, original upstream LGPL-2.1 and relevant third-party licenses. If redistributing, comply with all obligations.
- Test details: `docs/RUNTIME-TEST.md`.

## TPDP `notkey` compatibility concern
- Wine bug involving Japanese paths and SoD installer sometimes requires a symlink named `notkey` **in SoD folder**, pointing to base TPDP directory. Wine bug report: https://bugs.winehq.org/show_bug.cgi?id=54295 ; Steam Deck guide: https://gist.github.com/RobertTheSable/6c4d705623b4de8d8cb3c954eac4814f
- Reportedly fixed Wine 9.21; only enable symlink workaround if the actual selected Wine runtime needs it. The Kotlin helper does not automatically affect the runtime preview APK because they are currently separate builds.

## Immediate next implementation milestones
1. Have user install the **runtime preview** APK from successful GitHub Actions artifact, test that Winlator initializes and can create a container; gather crash/problem details.
2. Test **unpatched TPDP base game** in this self-contained runtime. Diagnose Wine graphics/font/input or Japanese locale issues, optimize Galaxy performance.
3. Merge dedicated Kotlin library/install wizard into the integrated runtime or port/bridge game-specific UI with upstream engine, so **one APK** does everything.
4. Add TPDP/SoD profile selection, safe installer EXE handling, Japanese path support and conditional `notkey` creation with verified target.
5. Add standalone English patch installers (with backups/version checks) then Extended DXGI override support.
6. Add touch gamepad/saves/restore and benchmark game-native frame pacing on device.

## Helpful links
- Repo: https://github.com/rgarn023/TouhouPocketLauncher
- Runtime build: https://github.com/rgarn023/TouhouPocketLauncher/actions/runs/39787333874
- Upstream engine: https://github.com/brunodev85/winlator-app
- Source changes: `runtime-preview/`
- Device testing: `docs/RUNTIME-TEST.md`

## Risks / honesty
- Engine preview is built and bundled, but ability to *install/run* TPDP on specific Android phone is unknown until device test.
- Independent English patches vary by game/version/format. Do not claim universal compatibility.
- Runtime preview and native alpha are two Android packages. This is intentional temporary scaffolding, not final one-APK UX.
