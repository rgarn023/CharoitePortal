# CHAROITE PORTAL / CHAROITE CORE — CURRENT PROJECT HANDOFF

**Current handoff updated:** October 27, 2026  
**Purpose:** Paste this entire file, or share its raw GitHub URL, in a new ChatGPT conversation to resume development.  
**Canonical copy:** `https://github.com/rgarn023/CharoitePortal/blob/main/docs/CURRENT_HANDOFF.md`  
**Raw / easy to copy:** `https://raw.githubusercontent.com/rgarn023/CharoitePortal/main/docs/CURRENT_HANDOFF.md`  
**Historical append-only development log:** `docs/HANDOFF.md` (begins in the old Touhou Pocket era; **not** current instructions).

> **MANDATORY:** GitHub's live `main` branch and its actual GitHub Actions state are always the source of truth. This file is a dated snapshot. After every substantive Charoite project response, **update this handoff in GitHub**, with actual changes/tests/build/device findings and specific next steps. Do not leave the user with a handoff that points to an outdated version when the conversation becomes slow. For documentation-only commits use `[skip ci]` to avoid building another 230 MB APK solely for a status note; check whether the previous successful APK still corresponds to the latest **code** commit.

## 1. Identity and non-negotiable workflow

- **Company:** Charoite Games. **Application:** Charoite Portal; common Wine runtime: Charoite Core.
- **Correct repository:** https://github.com/rgarn023/CharoitePortal
- **Only working branch:** `main`. **Android application ID:** `com.charoite`; legacy `com.touhoudr` is historical and **must not** be restored casually.
- **Primary target:** Android (Samsung Galaxy S26 Ultra), including Samsung DeX, phone portrait and landscape.
- **ChatGPT is the sole developer.** Directly inspect, edit, commit and test via the connected GitHub tools. Do not suggest Cursor, Gemini, agents, or pasteable coding prompts. The connection has **confirmed read/write access**.
- GitHub tools are available through `functions.exec`: search `ALL_TOOLS` for `mcp__GitHub__` methods; `fetch_file`, `update_file`, `create_file`, `fetch`, `fetch_workflow_run_jobs`, `fetch_workflow_run_artifacts`, etc.
- **Do not ask for repo uploads** if GitHub has the source. Fetch fresh `main` HEAD and exact file SHA before writes; commit directly to `main`, no new branches unless requested.
- **Never delete/clear app data, remove Wine prefixes, reinstall the app casually, or corrupt installed games, saves, wallpapers, shortcuts or environment data.** Signing/package changes require a demonstrated migration plan. Preserve game installations and user data through updates. Handle safety confirmations.
- **CI success does not establish phone/game compatibility.** Report actual device verification separately. Never claim an issue fixed on device solely on the strength of code/compilation.
- The user wants **frequent, concise progress reports** and this living handoff maintained after Charoite project responses. Use direct GitHub Actions artifact links, not invented or previously failing ChatGPT Library download links.

## 2. Current verified GitHub/APK state (October 27, 2026)

**Most recent successful APK before this handoff-documentation update:**
- **Runtime/code commit:** `8fa0194d93b8c28c6f3b82bd0b52cf162511b2ec`
- **Actions run:** **40564585687** — conclusion **success**; https://github.com/rgarn023/CharoitePortal/actions/runs/40564585687
- **APK artifact:** `Charoite-Portal-Android-APK` — artifact ID **12762049549**; reported compressed archive ~231 MB; present/not expired when last checked.
- **Tests:** 116 contract/regression tests passed; successful Android APK build, signing verification and upload in that run.
- **Phone validation:** The updated themed runtime drawer **has not yet been visually tested on the Galaxy**. The new CEF/login and cache tools are also awaiting the user's on-device report.

**Documentation housekeeping in this chat:** This canonical living handoff was added to the repository as a separate, easy-to-paste file; the root `README.md` now links here and retains a link to the historical handoff. These are documentation-only changes with `[skip ci]`; they do **not** require a new APK or replace the verified runtime build above. Always check `main` HEAD before development.

**Important:** Any new handoff-only commit may make `main` HEAD newer than the code SHA above without changing the APK. When resuming, inspect the current latest `main` SHA, commit differences, and Actions. If newer code exists, do not label the old build as the current code build.

**Earlier successful Battle.net diagnostic APK:** Actions run `40552092537`, code SHA `876222c7cc068bc0219cc71b703a75f5f40ea72d`, APK artifact ID `12756101469`. The newer run `40564585687` includes those fixes plus the drawer redesign.

## 3. Latest completed task — October 27 themed session menu

**User screenshot/problem:** The Windows session drawer was still the original gray/blue Winlator-style utility menu (Keyboard, Toggle Fullscreen, Task Manager, Active Windows, Magnifier, Screen Effect, PiP, Touchpad Help) with a generic Charoite Core header. User wants a Portal/environment-consistent theme, ideally only **Return to Charoite Portal**.

**Implemented directly on `main`:**
- `runtime-preview/overlay.py` changes committed at `3b87ed0a9919519bc5e852e3c29ddf6527816cd5`.
- The upstream `XServerDisplayActivity` drawer now shows **Return to Charoite Portal only** for handheld games and DeX. On **phone installers and login windows**, it additionally retains **Keyboard** for text entry when the existing handheld keyboard overlay is absent.
- Reuses the per-launch `charoite_environment_name` and `charoite_environment_theme` Intent extras already passed by `CharoiteGameSessions.java`, displays active realm name in drawer header and `CharoiteThemes.realmBanner(theme)` artwork. Touhou/sakura themes use pink/plum hues; other realms use the Charoite purple cosmic palette. Styles drawer item backgrounds, icon tint, text color.
- The existing Return action now goes through a **confirmation dialog for both game and installer sessions**, warning that quitting closes the Windows session and may lose unsaved game progress or interrupt an installer; **Stay Here** cancels. Existing exit teardown and Portal return remain intact.
- Preserves the Game Boy-style handheld shell and popup keyboard, input profiles, original Windows session utilities underneath, Wine/Box64, Battle.net monitor, and all user data; it only hides unnecessary drawer items.
- New `runtime-preview/tests/test_session_drawer_theme_contract.py` committed as `2b3f718e4a688728d1792d3b95091f5e51718f59` adds four regressions for menu scope, environment/theme source, safe exit and game input/data preservation.
- `runtime-preview/tests/test_tpdp_touch_controls_contract.py` updated for intentional new labels at `8fa0194d93b8c28c6f3b82bd0b52cf162511b2ec`. Earlier intermediate workflow attempts failed on two **stale test assertions**; after updating, run `40564585687` passed all tests and built/published the APK.
- **Next:** user installs the new same-package/same-signature update without clearing data and confirms portrait/landscape drawer appearance, environment-specific theming, whether Keyboard remains in Battle.net login where needed, confirmation and return behavior. Treat current status as **code/build verified, on-device unverified**.

## 4. Main unresolved functional issue — Battle.net endless spinner

Official Battle.net Windows installer was installed in dedicated **Battle.net Gaming** environment. Installer first crashed but subsequent install completed. The launcher/client displays a spinning interface indefinitely instead of finishing sign-in. The **root cause is unknown**.

**What was already implemented/tried, without a confirmed resolution:**
1. Original `Battle.net Launcher.exe`; direct `Battle.net.exe` startup bypassing bootstrapper.
2. Safe Browser `--disable-gpu`; opt-in WineD3D/VirGL vs DXVK/Vulkan and ESYNC/FSYNC off; session-only DLL `locationapi=d` and `WINE_SIMULATE_WRITECOPY=1`.
3. Explicit backed-up persisted `Battle.net.config` `Client.HardwareAcceleration=false`.
4. Read-only Agent logs, WinHTTP/DNS probe and same-session Agent/client process monitor.
5. New read-only CEF/browser preferences and categorized client logs; **optional reversible cache rename** added in last diagnostic build. Do **not** repeatedly reinstall launcher or delete Agent.

**Definitive monitored result from same active Wine session (16 samples):**
```
monitor_same_session=1
monitor_expected_samples=16
monitor_samples_completed=16
monitor_agent_present_samples=15
monitor_client_present_samples=16
monitor_launcher_present_samples=0
monitor_max_agent=1
monitor_max_client=5
monitor_complete=1
monitor_process_enumeration_error_samples=0
```
Agent.exe **does run** and client processes exist. The earlier standalone monitor reporting no Blizzard processes belonged to a *different* Wine activity and is **not** valid evidence of no Agent in the active session. Process presence alone does not prove Agent IPC, CEF renderer, login or authentication succeeds.

**Wine-side basic network probe:**
```
battle_net_dns_status=0
battle_net_https_phase=7
battle_net_https_win32_error=0
battle_net_http_status=200
downloader_dns_status=0
downloader_https_phase=7
downloader_https_win32_error=0
downloader_http_status=404
```
DNS/HTTPS work for tested endpoints. An HTTP 404 for downloader root is not necessarily an error. This does not prove auth endpoints, CDN completeness or Agent IPC.

**Most important next device evidence:**
- Go to **Battle.net Gaming → Setup → VIEW BATTLE.NET LOGIN / CEF REPORT** and share the report (designed not to expose secrets). It reads persisted hardware acceleration status and bounded aggregate counts for CEF/browser, GPU/compositor, Agent/IPC, network, crash/exception, and login/authentication.
- The larger **CHECK LAUNCHER + AGENT DIAGNOSTICS** and **VIEW LIVE AGENT MONITOR** remain available.
- Try the direct Safe Browser launch; note if still spinning. If desired, **fully close Battle.net first**, then explicitly confirm **BACK UP + RESET BATTLE.NET BROWSER CACHE**. This *renames/moves* supported local Cache/BrowserCaches/GPUCache/Code Cache folders to timestamped backups; it must not delete Agent, game installs, or preferences. It may or may not help. Recheck CEF report.
- New diagnostics should determine next targeted GitHub fixes: CEF subprocess/GPU/sandbox, inter-process Agent communication, cache/config, or bundled Wine/Box64 edge cases. **Do not assert any hypothesis is proven.**
- **Diablo IV / DX12 compatibility remains unverified.**

## 5. Architecture and code map

The application is **Charoite Portal** (Android frontend) plus a common **Charoite Core** (runtime/services). It still derives from pinned open-source Winlator foundation `brunodev85/winlator-app` SHA `8077f374ef2d54127b088de9e8cd7b4af14d9c8b` with Wine/Box64, XServer and Android graphics/input integration. Do **not** misrepresent this as an independent replacement for Winlator/Wine. No upstream-branded user-facing menu should leak; retain license notices.

- `runtime-preview/TouhouEntryActivity.java` — native Portal shell; Library, Setup, System; Battle.net UI and troubleshooting actions.
- `runtime-preview/charoite-core/CharoiteCore.java` — shared engine prep/compatibility policies.
- `runtime-preview/charoite-core/CharoiteGameSessions.java` — launch intent and active-environment snapshots; handheld vs installer vs DeX.
- `runtime-preview/charoite-core/CharoiteEnvironments.java` — separate environment registry, Wine container IDs, stable per-realm data paths; never confuse a different Activity's preferences with Portal's.
- `runtime-preview/charoite-core/CharoiteBattleNetSupport.java` — official installer/client discovery, diagnostics, cache backup.
- `runtime-preview/charoite-core/diagnostics/charoite_bnet_network_probe.c` — same-session Win32 monitor/network checks.
- `runtime-preview/charoite-core/CharoiteThemes.java` — original Charoite cosmic/Touhou sakura theme artwork.
- `runtime-preview/charoite-core/CharoiteTpdpTouchControls.java` — on-screen handheld buttons and popup keyboard.
- `runtime-preview/charoite-core/CharoiteWindowPolicy.java` — game/window scaling, orientation policy.
- `runtime-preview/charoite-core/CharoiteLegacyKeyboard.java` — crucial Touhou 8 scan-code bridge.
- `runtime-preview/overlay.py` — programmatic overlay onto pinned upstream Java/Android source. **Python strings generating Java require correct double escaping**, especially Windows paths; a previous CI failure was caused by illegal Java escapes.
- `.github/workflows/runtime-preview.yml` — complete signed APK build, native utilities, tests and packaging.
- `runtime-preview/tests/` — Python contract tests, including Battle.net preservation rules and new session drawer tests.

## 6. Product behavior and features to preserve

**Environments:** All environments share Core but have independent Wine C: drives/containers, libraries, theme/wallpaper, settings and isolated data. Built-ins: General Gaming, Touhou Realm, Battle.net Gaming. System supports switch/create/install/export `.cenv` settings profiles; these **do not** include full games or saves. Keep generated `C:\\CharoitePortal\\Environments\\<id>\\` data stable. Preserve legacy installations and user choices, don't overwrite selected environment.

**Library & Setup:** Library should only show explicitly consented game shortcuts. Removing a shortcut **does not uninstall game data**; users can re-add without reinstall. Show official icons when available. Selecting an installer folder **does not run arbitrary EXEs**; allow manual selection when multiple setup EXEs exist and launch one window. Actual removal of game files must be deliberate and confirmed.

**Handheld controls:** Transparent purple Game Boy-style shell; reliable equal-size D-pad and ABXY, Start/Select/shoulder and popup keyboard. Correct game-specific scan-code keyboard profiles. Touhou 8 mapping has been repaired; do not regress. Viewport must remain correctly scaled/framed, not drawn beyond bezel; support portrait/landscape and Galaxy tall displays. Hide Keys must also hide keyboard button. DeX/windows installers must not get a handheld overlay.

**Japanese/Touhou:** TPDP base and Shard of Dreams were made playable after DXVK+Turnip, Win32 CP932/locale font handling, graphics/window fixes. Existing Japanese installer rendering and Shard expansion paths need preservation. Game-specific compatibility should live in Core when reasonable, not require developer diagnostics toggled by end users. Don't bundle proprietary games or patches.

**Safety/labels:** No visible Winlator frontend; license attribution remains. Preserve package `com.charoite`, Wine saves/prefixes and settings. Preserve installable APK signing identity. Do not claim Battle.net/Diablo IV/any unverified title runs successfully because CI passed.

## 7. How to continue development and keep this handoff current

1. **First** obtain latest `main` SHA from GitHub and inspect latest Actions run/artifact; compare with this file. Read exact source, never work from stale memory.
2. For a reported bug, inspect underlying code and available diagnostics, make *minimal focused changes* directly to `main`, add/update tests and inspect CI job failures. Avoid broad refactors or deleting any user's data.
3. Await a successful build **of the actual latest code commit**; if CI is running/failed, explicitly report that. Link the successful GitHub Actions run and artifact name/ID. Device behavior needs actual user observation.
4. At the **end of every substantive response**, update **this file** with the latest changes/commit SHAs, source of truth, results, user feedback, outstanding bugs, and the exact first step for the next chat. Keep it concise, remove superseded *current-state* statements, preserve historically significant evidence.
5. On **handoff-only** edits, put `[skip ci]` in the commit message to avoid redundant APK compilation. If a documentation commit advances `main` beyond last successful runtime commit, state so explicitly rather than claiming CI built that doc commit.
6. Provide user the canonical [current handoff](https://github.com/rgarn023/CharoitePortal/blob/main/docs/CURRENT_HANDOFF.md) whenever context becomes long, so they can copy the raw Markdown into a new conversation. The old `docs/HANDOFF.md` is useful only as historical provenance.

**Next user-facing action as of this snapshot:** test the new themed session drawer using APK from run `40564585687`, then share its visual behavior. When ready to resume Battle.net spinner diagnosis, share **VIEW BATTLE.NET LOGIN / CEF REPORT**. Do not start speculative changes before receiving device evidence unless the user requests another task.

---
**End of current Charoite Portal handoff.**
