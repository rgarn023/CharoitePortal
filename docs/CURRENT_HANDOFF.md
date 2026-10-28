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

**Latest verified Android runtime APK (source code):**
- **APK source SHA:** `553d9cbd8dc49edc84016fda2adc83cb27c031b5`.
- **GitHub Actions run `40641148611` — SUCCESS:** https://github.com/rgarn023/CharoitePortal/actions/runs/40641148611
- **APK artifact:** `Charoite-Portal-Android-APK`, ID **12795777267**, uploaded/nonexpired; ZIP **231,433,090 bytes**.
- **Tests:** **138 regression tests passed** in final Actions logs; full Android signed APK and native Windows diagnostic helper build succeeded.
- **Observed phone outcome:** User explicitly confirmed **"Still spinning"** following October 28 00:13 EDT diagnostic from APK run `40627760121`. RPC prelaunch ready/rollback, Agent present, 4/4 Agent listener tables with example port 38789, zero sampled Battle.net→Agent IPv4 matches. 83 log error-like entries include rendering/GPU categories but overlap/historic lines. The user has NOT explicitly confirmed which RPC dialog option was selected or whether browser-cache backup/reset was attempted.
- **New APK change:** Android-side, numeric-only **BATTLE.NET LAUNCH FINGERPRINT** in **VIEW BATTLE.NET LOGIN / CEF REPORT** and live monitor, recording intent/requested mode versus actual assembled `--disable-gpu` flag and resolved renderer/WineD3D, plus effective ESYNC/FSYNC and locationapi rule before Wine receives environment. Timestamps and stale/missing snapshot warnings. No raw command lines, credentials, Blizzard files or registry data exposed, no login result inference.
- **Preserve:** `com.charoite`, existing game installs/saves, Wine prefixes and Blizzard Agent and cache. No destructive changes. Handoff-only `[skip ci]` commits advance main beyond APK source SHA without a rebuild.
- **Existing next recovery option:** User-controlled **BACK UP + RESET BATTLE.NET BROWSER CACHE** after fully closing Battle.net, backing up only selected `AppData/Local/Battle.net` cache folders; no automatic `ProgramData/Battle.net` deletion.

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

**Current priority (October 28):** Battle.net sign-in remains **spinning**, explicitly confirmed by user following prior 00:13 report. Existing RPC before-client startup and rollback WORK (16/16 RUNNING), Agent listening, Battle.net subprocesses alive. No sampled direct IPv4 connection to Agent listener in four snapshots, inconclusive. Prior diagnostics did not distinguish **RPC + graphics** vs **Try once**, nor prove that WineD3D/VirGL or `--disable-gpu` flags reached client. New successful APK run `40641148611` (SHA `553d9cbd...`) adds Android-originated **launch fingerprint** to the login report showing numeric requested flags and resolved launcher choices plus effective Wine env, without logging personal data. **This is a diagnostic, not a fix**; user has not yet installed/tested new APK. Recommend user safely update in place, close all Battle.net/Agent sessions, use existing opt-in **BACK UP + RESET BATTLE.NET BROWSER CACHE** which only renames select local browser caches to timestamped backups, then run **TRY BATTLE.NET (START WINE RPC SERVICE) → RPC + graphics** and send the new full report plus visible outcome. If they already performed cache reset, don't repeat unnecessarily; capture fingerprint and investigate CEF-specific renderer/IPC. Do NOT continually mutate RpcSs, delete Agent files, use the historical port 1120 to infer error, wipe prefix, or replace Wine without evidence.

## 8. October 27, 2026 — Windows 11 compatibility / next Battle.net engineering plan (research only)

**User question:** "What's next for battle.net? Can we make the environment suitable for windows 11 applications and games? Would that require modifications to wine?"

**Answer and scope:** Yes, Charoite Core can aim for modern Windows 10/11 *application compatibility*, but it will not run an actual copy of Windows 11. A Windows 11 OS-version profile alone does not implement missing Win32 APIs, DirectX 12, DRM, anti-cheat/kernel drivers or GPU features. **No runtime implementation was requested explicitly or committed in this discussion; this section records verified research and proposed engineering stages only.**

**Verified source inspection (GitHub live `main` and pinned upstream):**
- Pinned Winlator-derived source: `brunodev85/winlator-app` at SHA `8077f374ef2d54127b088de9e8cd7b4af14d9c8b`. Its `WineInfo.MAIN_WINE_VERSION` is **Wine 10.10 custom**; `DefaultVersion.BOX64 = "0.4.4"`; `DXVK = 2.4.1` (plus legacy 1.10.3); `VKD3D = 2.14.1` is **defined**, not verified as successfully running DirectX 12 on the device. Turnip, Vortek, VirGL and Zink are among included graphics choices.
- The upstream Wine **10.10** source `programs/winecfg/appdefaults.c` already contains `win11` with Windows 11 reported version/build (10.0, 22000), plus `win10` default. Thus **do not patch or fork Wine just to claim a Windows 11 version selection**. Confirm the actual bundled custom build recognizes `win11` at runtime before promising a UI toggle. Official Wine 11.0 was released Jan. 13, 2026 and contains substantial WoW64 and other compatibility improvements, but is **not bundled** by this pinned baseline.
- Pinned upstream `DXWrappers` defines `VKD3D`, but `parseIdentifier()` only accepts `WINED3D` or `DXVK`; thus a modern DX12 stack/actual VKD3D selection **cannot be assumed** from the constant. Prove that compatible D3D12 DLL/DXGI and Vulkan 1.3/features are installed/configured and working rather than presenting a misleading label.
- Official Blizzard Diablo IV Windows minimum is **Windows 10 1909+**, **DirectX 12**, SSD and 90 GB space, 8 GB RAM minimum; setting Windows 11 is **not required** for its published base OS requirement. Charoite Android/Box64/GPU compatibility and game sign-in/anti-tamper remain **unverified**.
- Wine version/profile changes can alter Wine prefix state. **Do not automatically upgrade the existing Battle.net or Touhou Wine containers** to Wine 11, change package ID or replace DXVK/VKD3D. Test separately with explicit backups and rollback.

**Public research references to recheck on next iteration:**
- Official Wine 11.0 news: https://www.winehq.org/news/2026011301
- Wine 10.10 Windows version choices: https://github.com/wine-mirror/wine/blob/wine-10.10/programs/winecfg/appdefaults.c
- Bundled upstream Wine version: https://github.com/brunodev85/winlator-app/blob/8077f374ef2d54127b088de9e8cd7b4af14d9c8b/app/src/main/java/com/winlator/core/WineInfo.java
- Upstream graphics wrapper configuration: https://github.com/brunodev85/winlator-app/blob/8077f374ef2d54127b088de9e8cd7b4af14d9c8b/app/src/main/java/com/winlator/container/DXWrappers.java
- DX12 translator requirements (VKD3D-Proton): https://github.com/HansKristian-Work/vkd3d-proton
- Blizzard Diablo IV original requirements: https://news.blizzard.com/en-us/article/23938756/make-sanctuary-yoursplay-your-way-in-diablo-iv

**Prioritized implementation plan, NOT yet implemented:**
1. **Battle.net first, no destructive change:** On current successful APK run `VIEW BATTLE.NET LOGIN / CEF REPORT`, observe login UI/cache/CEF/renderer/IPC category counts; optionally compare SAFE BROWSER launch and explicitly confirmed cache backup after closing client. Then use targeted, bounded same-Wine-session probes to test CEF subprocess status, IPC and errors, without credentials. Do not assume lack of Agent; monitor showed Agent 15/16 samples.
2. **Guest compatibility audit/probe:** From same prefix determine actual Wine version; OS version via `winecfg`/system calls; DXVK/DXGI/D3D12 DLL status; GPU Vulkan version/features; CEF subprocess creation. Expose only sanitized details in Setup Diagnostics.
3. **Isolated modern Windows version profile:** Add per-environment (optionally per-app) **Windows 10 / Windows 11** version reporting, default current working state and don't change Touhou behavior. Validate `win11` actually works on bundled Wine. Make preference explicit and reversible; avoid unconditional mass prefix edits. This affects version reporting, NOT underlying Windows feature set.
4. **Modern runtime option, if evidence requires it:** Investigate Wine 11.x/compatible stable guest build as optional separate runner in a test environment (or copy/backup prefix), with Android/Box64 and user-space compatibility, import/switch and rollback. Do not hot-swap live game prefixes or silently migrate.
5. **DirectX 12 readiness stage:** Test/select bundled VKD3D-Proton and DXVK DXGI alongside Turnip Vulkan feature/extension requirements and 64-bit guest. Only label a modern game DX12-compatible after a real D3D12 smoke test (then actual game). No guarantee Diablo IV will run; its launcher and DRM/anti-tamper need independent checks.
6. Add contract/CI tests, GitHub Actions signed APK verification, and Galaxy on-device results for each stage. Preserve all existing setups.

**Immediate next action:** user supplies the new `VIEW BATTLE.NET LOGIN / CEF REPORT` from the latest APK, or explicitly requests implementing the Windows version profile first. Work directly in GitHub with tests and APK build, update this handoff again. `main` was `703d37ddb872725a0d0db080d09c5729afa23ec1` when starting this documentation update; this *documentation-only* commit will advance HEAD but should not trigger another APK build.

## 9. October 27, 2026 — Battle.net CEF/RPC work, successful build

**Request:** Get the Battle.net launcher past endless spinner before testing Diablo III/IV. Android-native Diablo Immortal performance alone does not prove Windows x86/DX graphics compatibility. Diablo III is a more tractable first test (D3D9/11); Diablo IV needs DirectX 12 and considerably more compatibility work.

**Changes committed to `main`:**
- `bf2640957434d2d32474c59f66045e570ec0b9c2`: Extend Charoite's existing 16-sample, same-session Wine guest process monitor to count **rpcss.exe** and **services.exe** presence. New report fields `monitor_rpcss_present_samples`, `monitor_services_present_samples`, `monitor_max_rpcss`, `monitor_max_services`. Service process presence is NOT proof RPC works.
- `0585e91eaa0053f8c31f0d9dfaf0d20dfbc81d76`: Extend `CharoiteBattleNetSupport.inspectInSessionAgentMonitor()` report explanations with new Wine service counts and backward-compatible old-report notice.
- `90097b8b48e4bffc00bb688724f0b407297ba88f`, `7687b6019c0feaceb9444a1a883fd019e3785e1e`: Add optional **`--in-process-gpu`** command-line experiment, explicitly scoped to `Battle.net.exe` or `Battle.net Launcher.exe` in Battle.net environment. It is mutually exclusive with `--disable-gpu`, per launch only, with no persistent Wine, game or Agent modifications.
- `97747f9f642fa56a8a5fbbfa9e9b94e0fb5f31fc`: Battle.net Setup adds **TRY BATTLE.NET (CEF GPU PROCESS TEST)**. Dedicated **VIEW BATTLE.NET LOGIN / CEF REPORT** now includes same-session Wine process monitor, saved browser preferences, and classified client logs in one copyable report. Original/Safe Browser/compatibility/cache-backup routes remain.
- `9616d090ac3930687fc732003177e394c840aae3`: Added regression test `test_battlenet_cef_rpc_contract.py`; regular tests and Android build succeeded.

**Verified GitHub Actions APK:** https://github.com/rgarn023/CharoitePortal/actions/runs/40568654996 — conclusion **SUCCESS**, code SHA **`9616d090ac3930687fc732003177e394c840aae3`**. Artifact **`Charoite-Portal-Android-APK`**, ID **12764561868**, ~231 MB compressed, present and not expired at last check. Compilation, signing and artifact publishing passed. **Still untested on Galaxy.** Documentation-only handoff commit after this advances main HEAD, NOT the APK source code.

**Immediate, precise next action:** Update existing `com.charoite` installation without uninstall/clear-data, from run `40568654996`. Under **Battle.net Gaming → Setup**, choose **TRY BATTLE.NET (CEF GPU PROCESS TEST)**. Observe whether the spinner remains or sign-in appears. Keep client visible ~30 seconds; return to Portal and click **VIEW BATTLE.NET LOGIN / CEF REPORT** → **Copy report**. Share entire sanitized report with ChatGPT (new rpcss/services counts plus CEF and saved GPU settings). For meaningful comparison, close the client before trying **OPEN BATTLE.NET (DIRECT SAFE BROWSER)** separately. Do not auto-apply cache reset or modify Agent without explicit consent.

**Diagnosis boundaries:** If `rpcss` or `services` is repeatedly missing, investigate Wine service startup/IPC. If both present and spinner persists, investigate CEF subprocess/rendering and Agent IPC with more targeted bounded probes. A July 2026 Proton ARM64 installer report described an RPC retry loop, but this is a different symptom and does **not** prove root cause here. The `--in-process-gpu` option is a hypothesis-driven experiment, not a proven repair. Do not claim Battle.net or Diablo III/IV working without device validation. Preserve Touhou controls, Japanese support, environment C: drives and all installed games/saves.

## 10. October 27, 2026 — User's actual Battle.net report + successful RpcSs service-state diagnostic APK

**User provided actual phone diagnostic** for the prior `40568654996` APK:
- `monitor_same_session=1`, `monitor_complete=1`, completed **16/16** samples; no enumeration errors.
- Battle.net client in **16/16** samples, Blizzard Agent **15/16**, Wine `services.exe` **16/16**, but Wine process named `rpcss.exe` in **0/16**. Agent/client alive does not prove login or IPC; absence of process name does not prove RpcSs service is stopped.
- Browser settings file count 1, hardware acceleration OFF; 6 log files, 125 error-like lines; GPU/compositor 39, rendering 24, CEF/browser 2, Agent/IPC 3, network 5, crash/exception 1, login/auth 2. These are overlapping keyword counts, not confirmed root-cause events.
- Do **not** assume `--in-process-gpu` solved the spinner: user has **not said** whether it changed the visible symptom.

**New focused improvements in GitHub, all non-destructive:**
- `868afadde5b6f3f92595c376ca3f97029b7449d7` Win32 guest helper queries `RpcSs` via SCM APIs `OpenSCManagerW(SC_MANAGER_CONNECT)`, `OpenServiceW(SERVICE_QUERY_STATUS)`, `QueryServiceStatusEx`; records sanitized numeric running, stopped, failed counts and Win32 error codes across same 16-sample Wine monitor. Does **NOT** start, stop, reconfigure services or change files/registry.
- `5fe0a149cf9b6f924ba6153168f225539951b810` adds Advapi32 linker dependency for this helper.
- `7cb98028590027b329cedc5d0df33fc9c7947ed0` upgrades monitor interpretation, removes repetitive intermediate sample-count lines, correctly describes observed Agent/client, and reports actual SCM service status rather than inferring it from process names. Older report remains recognizable.
- `6c0cdae24ea94e6a214f125f1fa03dc542a0f971` adds coarse error categories specifically for GPU-process issues, device loss, memory protection, and RPC/service-manager, without displaying raw logs/account identifiers.
- `6d7d6be0e19dbe030da461b83272f0362ae783ed` added safe service/CEF regression tests. Intermediate run `40571366268` failed a stale assertion in older tests, fixed by `1ef29980e27045aad1b9f44862b050133cfe52de`. New code/build **SUCCESS**: run `40571495554`, artifact `Charoite-Portal-Android-APK` ID `12766230073`.

**Exact next device step:** update installed `com.charoite` APK from https://github.com/rgarn023/CharoitePortal/actions/runs/40571495554 **without uninstalling or clearing data**. Launch Battle.net in Battle.net Gaming realm, keep running ~30 seconds; return to Portal, copy **VIEW BATTLE.NET LOGIN / CEF REPORT** (or VIEW LIVE AGENT MONITOR) and provide counts `monitor_rpc_service_running_samples`, `monitor_rpc_service_stopped_samples`, `monitor_rpc_service_query_failed_samples`, `monitor_rpc_scm_error_last`, `monitor_rpc_open_error_last`, `monitor_rpc_query_error_last` plus refined CEF GPU categories and whether browser spinner persists. Running/absent service conclusions must come from SCM query, not name inference. No runtime fix has yet been validated on Galaxy.

## 11. October 27, 2026 — Possible future Google Play commercial release / ads

**User asked:** once fully working, can Charoite Portal be monetized as a paid Google Play app or free with advertising? **Answer: potentially yes, but only after compliance and distribution work; neither approval nor profitability is assured.** Do not implement ad SDK or paid features until user decides the model.

**Licenses:** pinned `brunodev85/winlator-app` base has LGPL-2.1 source; commercial distribution is permitted if obligations are satisfied (source availability, notices, modified portions/relinking where required). Audit **all components** (Wine, Box64, Mesa, DXVK, VKD3D, fonts, art, any proprietary DLL dependencies) individually. Current project bundles upstream notice/license + source archive in Actions, but that alone is **not a legal compliance certification**. Do not imply a proprietary exclusive right over upstream code. Avoid shipping unlicensed Blizzard/Touhou/Diablo executables, assets, logos or misleading trademark/official-association claims; let users provide games they own.

**Key verified blockers in current source (do not confuse old `app/` Kotlin variant with actual Wine runtime build):**
- Actual runtime built from pinned upstream `app/build.gradle` has **`targetSdkVersion 28`** and `compileSdk 35` (overlay only changes `applicationId` and signing, not target). As of **Aug 31, 2026 Google Play new Android apps/updates require target API 36** (possibly eligible extension through Nov 1); migrating a Wine/Box64 app from target 28 to 36 needs deep Android storage, native exec, 16KB pages, system and foreground-service behavior audits. This is a substantial release engineering project.
- GitHub workflow currently builds signed **`assembleDebug` APK**, not Google Play-ready **signed Android App Bundle (AAB)**. Must add separate Play production flavor/process, increment versionCode, secure production signing/Play App Signing, and test update/migration from existing debug signature without loss of `com.charoite` private Wine data.
- Bundle compressed artifact approximately **231 MB**. Google currently lists **500MB base module** Play size cap, with >200MB mobile-data notice; verify true per-device AAB compressed size in Play Console and optimize if needed. See https://support.google.com/googleplay/android-developer/answer/9859372
- Google's device/network-abuse policy forbids app self-updates outside Play and limits downloading Android executable code from elsewhere, with a **VM/interpreter exception**. Charoite downloads Windows `.exe` inside Wine: must evaluate actual architecture and policy (and third-party network terms) rather than assume exception or approval. https://support.google.com/googleplay/android-developer/answer/16559646
- Google Play IP policy forbids infringement and confusing trademarks: https://support.google.com/googleplay/android-developer/answer/9888072
- Monetization options include paid Play listing or free with tasteful Portal-only banner/native ads and optional paid ad-removal via compliant Play Billing. **Do not put ads over gameplay, installers, login, controller overlays or sessions.** Respect Play ads policy, clearly disclose ads, provide privacy policy/Data Safety/consent as applicable. https://support.google.com/googleplay/android-developer/answer/9857753 and https://support.google.com/googleplay/android-developer/answer/10787469
- Play developer registration currently **US$25 one time**. New *personal* developer accounts created after Nov 13 2023 generally need **12 continuously opted-in closed testers for 14 days** before applying for production access. https://support.google.com/googleplay/android-developer/answer/6112435/ and https://support.google.com/googleplay/android-developer/answer/14151465

**Recommended future roadmap:** solve core Battle.net/game UX first, document real hardware/device matrix, audit LGPL/other licenses and IP, modernize runtime for API 36, build a production AAB and signing migration, complete privacy and Play review/closed testing, then choose pricing or ads. Do not claim store-ready now. Keep the existing downloadable APK development workflow separate from eventual Play distribution.

## 12. October 27, 2026 — On-device RpcSs STOPPED confirmed; new opt-in start test successfully built

**Actual Galaxy report (17:01 EDT; prior APK run 40571495554):**
```
monitor_same_session=1
monitor_expected_samples=16
monitor_samples_completed=16
monitor_agent_present_samples=15
monitor_client_present_samples=16
monitor_max_client=5
monitor_rpcss_present_samples=0
monitor_services_present_samples=16
monitor_rpc_scm_connect_success_samples=16
monitor_rpc_service_running_samples=0
monitor_rpc_service_stopped_samples=16
monitor_rpc_service_query_failed_samples=0
monitor_rpc_service_state_last=1
monitor_rpc_scm_error_last=0
monitor_rpc_open_error_last=0
monitor_rpc_query_error_last=0
monitor_process_enumeration_error_samples=0
monitor_complete=1
```
`SERVICE_STOPPED=1` is a **genuine SCM status**, not merely a missing rpcss.exe filename. Meanwhile Battle.net and Agent are live, so the exact causal relation to endless spinner is still unknown. One browser config has `HardwareAcceleration=false`; six sampled client logs: 138 error-like entries, 44 GPU/compositor, 40 rendering, 9 GPU-process, 4 Agent/IPC, 6 network, 3 login/auth, 3 CEF, 0 device lost, 0 memory-protection, 0 matching RPC keywords. These are overlapping text category counts, not proven GPU crashes. User has **not** yet confirmed success/failure of prior `--in-process-gpu` experiment.

**Evidence motivating targeted test:** Wine's own `rpcrt4/rpc_epmap.c` implements service activation through `OpenServiceW(..., SERVICE_START | SERVICE_QUERY_STATUS)` and `StartServiceW`. The on-device stopped status justifies testing explicit activation, but not a blanket system rewrite. Source: https://github.com/wine-mirror/wine/blob/master/dlls/rpcrt4/rpc_epmap.c

**Implementation DIRECTLY in GitHub main, no user file uploads:**
- `52888718377fb258fbf2bf2000918682aa488fff`, `b21473babd8a9759fafb8cde3a9d4162fcae7db5`: update bundled first-party Win32 `charoite_bnet_network_probe.c` with **optional `/monitor /try-rpcss-start`**. On explicit flag only, query current RpcSs status, call `StartServiceW` only when it was `SERVICE_STOPPED`, poll bounded time, and log `monitor_rpc_start_before_state`, `monitor_rpc_start_attempted`, `monitor_rpc_start_win32_error`, `monitor_rpc_start_after_state`, SCM/open/query errors, etc. **Ordinary `/monitor` remains read-only**. Never change service startup mode, registry, installed Blizzard files, game files or any save. Note the helper is dispatched via `WinHandler.exec` **after Wine's display bridge is ready**; it is not a pre-executable startup hook. Initial behavior may already have failed before repair triggers; report actual results.
- `06b5a4cbfc9f30405c058e7b2b65824add338447`: `CharoiteGameSessions.launch` gains a boolean `tryStartBattleNetRpc` overload and sanitized `charoite_bnet_try_start_rpc` Intent extra, restricted to **installed `Battle.net Launcher.exe` / `Battle.net.exe`** inside **Battle.net Gaming**, never installers/Touhou/other environments. All existing overloads retain default false.
- `d8503d179835db53f4ec09804e42ea378760ffa3`: `runtime-preview/overlay.py` selects `/monitor /try-rpcss-start` only when scoped Intent flag is true; otherwise sends original `/monitor`.
- `9bebc0e5aced23ae718c62696e65cb29f66a38ab`: Battle.net Setup adds **TRY BATTLE.NET (START WINE RPC SERVICE)** with explicit dialog **Try once**/**Cancel**. It launches the installed client in a normal Windows session with Safe Browser `--disable-gpu` and requests the one-session opt-in helper start. User should fully close any earlier Battle.net sessions first. Clearly warns no guarantee or permanent service change.
- `54a54404bf6be4f7138801c1a987b3c675ac2b04`: live monitor reports whether opt-in was attempted, and before/after SCM service state and any start error, alongside client/Agent status. Note `RUNNING=4`, `STOPPED=1`.
- `232829bdd6622b63e5bd68088d488c543ce42a42` creates new opt-in scope/safety contract tests; `b31049a52c1d69e8bf35a87ecd9822968ab5ac1e` updates the old **read-only** monitoring test to allow mutation only behind explicit opt-in. Intermediate CI runs failed stale assertions, final suite and full APK compilation succeeded.
- **Verified latest APK:** Actions https://github.com/rgarn023/CharoitePortal/actions/runs/40584206916 **SUCCESS**, runtime SHA `b31049a52c1d69e8bf35a87ecd9822968ab5ac1e`, artifact `Charoite-Portal-Android-APK` ID **12770927138**. This handoff-only update uses `[skip ci]` and advances main HEAD after this code/build.

**NEXT STEP for new chat:** Ask user to install update over existing `com.charoite` (do **not** uninstall/clear storage), ensure old Battle.net Windows session is closed, open Battle.net Gaming → Setup → **TRY BATTLE.NET (START WINE RPC SERVICE)**, confirm, observe UI; after 30 seconds return and copy **VIEW BATTLE.NET LOGIN / CEF REPORT**, especially:
`monitor_rpc_opt_in_start_requested`,
`monitor_rpc_start_before_state`,
`monitor_rpc_start_attempted`,
`monitor_rpc_start_win32_error`,
`monitor_rpc_start_after_state`,
`monitor_rpc_service_running_samples`,
`monitor_rpc_service_stopped_samples`, GPU categories; user should say whether spinner or login appears. If service reaches running but spinner persists, focus CEF GPU/Agent IPC; if fails, investigate exact Win32 error/service binary. Don't claim Diablo III/IV support or Battle.net login fixed until on-device verified.

## 13. October 27, 2026 — RpcSs StartService error 1058; temporary startup-type repair APK built

**New real Galaxy report supplied by user (17:17 EDT):** They selected **TRY BATTLE.NET (START WINE RPC SERVICE)** in run `40584206916`. Confirmed `monitor_rpc_opt_in_start_requested=1`, `monitor_rpc_start_before_state=1` (STOPPED), `monitor_rpc_start_attempted=1`, and **`monitor_rpc_start_win32_error=1058`**. Wine service remained STOPPED in 16/16 samples; SCM connect successful in 16/16 with zero query/open errors. Battle.net client present 16/16 samples (max 5 processes); Agent present 15/16. Saved browser hardware acceleration OFF. Six logs: 118 error-like lines, 52 rendering refs, 16 GPU/compositor refs, 13 GPU-process refs, 3 CEF refs, 3 Agent/IPC refs, 6 network refs, 3 login/auth refs. No confirmed login success; never assert error counts themselves identify a GPU fault.

**Interpretation:** Microsoft identifies Win32 **1058** as `ERROR_SERVICE_DISABLED`: the service cannot start because it is disabled or there are no enabled associated devices. This makes original STARTUP TYPE inspection the next logical test; a blind retry of `StartServiceW` alone would be ineffective. Source: https://learn.microsoft.com/en-us/troubleshoot/windows-client/performance/error-1058-displayed-when-service-stops . The Wine RpcSs role is documented in `wine-mirror/wine:dlls/rpcrt4/rpc_epmap.c`. The exact reason Wine's custom Battle.net prefix has it stopped/disabled remains to be established. User has not verified the GPU-process trial resolves spinner.

**New implementation on existing `main`:**
- `2aa33c527f76122c1c99ec1ab42ba93ca526e7c8`: extend read-only same-session Wine SCM probe `charoite_bnet_network_probe.c` with `QueryServiceConfigW` start type and bounded config errors; report per-sample disabled/manual counts, last start type, and Win32 query errors. Normal non-opt-in monitoring remains read-only.
- `8ea1f5ef0016c919b2679934f0e028104d24181b`: the already-explicit Battle.net-only `/monitor /try-rpcss-start` mode now **only if start type is exactly `SERVICE_DISABLED`**: save a fixed-format marker `C:\\CharoitePortal\\Diagnostics\\charoite_rpcss_recovery.txt` in the active Wine container and fsync it; temporarily call `ChangeServiceConfigW` to `SERVICE_DEMAND_START`; call `StartServiceW`, poll bounded status, then call `ChangeServiceConfigW` back to original `SERVICE_DISABLED`; query and confirm rollback, then remove marker. Failed or interrupted restore retains marker, and a **future explicit opt-in attempt first tries to restore Disabled safely** before another attempt. Never modify other realms, Agent, games, or service startup policy permanently as a feature. A crash between change/restore can leave startup type Manual until opt-in recovery; report clearly and do not conceal risk. `aa29752deebe5708c6d823384107e701f450c0a2` completes necessary C string header for native compilation.
- `196200df49b9be2313b776c5b5dba5b5621d429c`: revises Battle.net Setup explanatory text and confirmation: this experiment **temporarily changes service startup** and attempts restoration, warns about interrupted rollback and instructs to close prior client sessions and keep it open ~30 s. Button remains **TRY BATTLE.NET (START WINE RPC SERVICE)**. Existing launch scoping in Core and monitor wiring preserved.
- `b65dd6ad6b74754d0cdaa38f84fcdfa36cc70106`: report now explains `monitor_rpc_config_disabled_samples` / start type, temporary-enable outcome, and **confirmed vs unconfirmed rollback**, with exact errors.
- `43af440e6294aa2a11fee249ba01086579548d50`, `15549330124067cb0f8c46b24e0e9ca0702bf18b`, `ca0cc5ebef33434d223e71a1dfd219a5a9027ff6`, `fc30b98b033ef67a1ba7e7a8d0f430e275be0117`: update contract tests for read-only /monitor versus opt-in-only service changes, recovery marker and UI consent. Older intermediate CI runs failed stale test wording, not confirmed runtime problems; latest code run **PASS**.
- **Verified build:** GitHub Actions https://github.com/rgarn023/CharoitePortal/actions/runs/40586875588 **SUCCESS**, source SHA **`aa29752deebe5708c6d823384107e701f450c0a2`**, APK artifact **`Charoite-Portal-Android-APK`** ID **12772202008** (231,423,080 bytes ZIP, unexpired). Package ID `com.charoite`; install as update without uninstall, clearing any storage or destroying saves.

**Immediate next precise phone test:**
1. Download APK from successful run `40586875588`, update existing installation without deleting app/prefix data; fully close other Battle.net sessions.
2. Under **Battle.net Gaming → Setup**, explicitly choose **TRY BATTLE.NET (START WINE RPC SERVICE)** and confirm the warning about temporary startup-mode change. Keep the Wine session open at least ~30 seconds.
3. Observe whether spinner changes to login; return to Portal → **VIEW BATTLE.NET LOGIN / CEF REPORT** → Copy report.
4. Inspect `monitor_rpc_start_before_type` (expected 4=Disabled, but **must verify**), `monitor_rpc_temporary_enable_attempted`, `monitor_rpc_temporary_enable_error`, `monitor_rpc_start_win32_error`, `monitor_rpc_start_after_state` (4=Running), `monitor_rpc_restore_confirmed` (must be 1 if a temporary change was made), `monitor_rpc_restore_error`, `monitor_rpc_recovery_error`, `monitor_rpc_start_type_after` (expected original 4), and running/stopped samples. If restoration NOT confirmed, do not casually repeat/run arbitrary repairs; use the recovery marker state and investigate.
5. If RpcSs now running but login spinner persists, focus on CEF subprocess and Agent IPC. If service cannot be configured/started or restored, diagnose its exact Win32 status, service binary and running user context before changing Wine or wiping data. Treat this as an opt-in compatibility experiment, not a proven Battle.net repair.

## 14. October 27, 2026 — Verified on-device success of RpcSs start AND rollback; login outcome not yet known

**Direct user report (17:43 EDT from APK GitHub Actions `40586875588`, code SHA `aa29752deebe5708c6d823384107e701f450c0a2`):**
- `monitor_rpc_opt_in_start_requested=1`, `monitor_rpc_start_before_state=1` (STOPPED), `monitor_rpc_start_before_type=4` (DISABLED)
- `monitor_rpc_temporary_enable_attempted=1`, `monitor_rpc_temporary_enable_error=0`
- `monitor_rpc_start_attempted=1`, `monitor_rpc_start_win32_error=0`, `monitor_rpc_start_after_state=4` (RUNNING)
- `monitor_rpc_restore_attempted=1`, `monitor_rpc_restore_error=0`, `monitor_rpc_restore_confirmed=1`, `monitor_rpc_start_type_after=4` (restored DISABLED)
- `monitor_rpc_recovery_marker_pending=0`, `monitor_rpc_recovery_error=0`
- **RpcSs service RUNNING and rpcss.exe present in all 16/16 samples**, service-manager connected in all 16; no service query errors or process enumeration errors; Blizzard Agent present 15/16, Battle.net client present 16/16.
- Saved browser acceleration OFF in 1 config. Most recent 6 Blizzard client logs: 97 error-like lines, 40 rendering refs, 13 GPU/compositor refs, 10 GPU-process refs, 3 CEF refs, 3 Agent/IPC refs, 6 network refs, 3 login/auth refs, no crash refs. Counts overlap, may contain errors from previous launches, and aren't a definitive root cause.
- **Critical unreported fact:** The user pasted monitor output but **did NOT state whether the Battle.net spinner disappeared or a login screen appeared.** Do not claim Battle.net fixed. The runtime repair and restoration **are independently verified as working on phone**.

**Source review this turn (read only; no application code changes or new APK):**
- Pinned upstream `brunodev85/winlator-app` SHA `8077f374ef2d54127b088de9e8cd7b4af14d9c8b`, `app/src/main/java/com/winlator/XServerDisplayActivity.java`, method `setupXEnvironment`: constructs Wine command via `getWineStartCommand()`, adds `GuestProgramLauncherComponent`, then `environment.startEnvironmentComponents()` which starts the Windows client. `getWineStartCommand()` uses `wine explorer /desktop=... C:\\windows\\winhandler.exe /dir <app> ...` as application launcher.
- The Charoite hook `startCharoiteBattleNetMonitor()` is triggered from `onMapWindow` when a renderable window first opens, and only after WinHandler keyboard bridge becomes ready does it run the Win32 helper via `winHandler.exec(..., "/monitor /try-rpcss-start")`. **Thus RpcSs is started after initial client launch, not before the first CEF initialization.** The observed service availability could be too late for an earlier failed CEF login bootstrap. This is a **plausible timing hypothesis, not yet proven**.
- The opt-in temporary change already restored original service start type correctly, so don't change settings persistently or undo working fix without new evidence.
- **Next action:** Ask user whether the Battle.net screen reached sign-in after `RpcSs` ran. If yes, proceed to Blizzard login interaction and then Diablo III installation testing, carefully protecting credentials and legal game ownership. If it still spins, prioritize a **pre-client-start** scoped RPC bootstrap mechanism (or a controlled one-session CEF restart after RpcSs is running) *before* further broad Wine version or registry changes. Ensure rollback is robust on process failure, cancel, and screen rotation. Then investigate CEF GPU/log categories and Agent IPC. Keep CI and APK verification and living handoff updated.

## 15. October 27, 2026 — Battle.net still spins with RPC running; BEFORE-CLIENT launch gate implemented

**New user-confirmed fact:** User stated **"It's still spinning"** after last Galaxy report proved `RpcSs` was RUNNING in 16/16 samples, a previously disabled startup type was restored and Blizzard Agent/client processes remained present. Therefore this eliminates mere **lack of running RpcSs at monitoring time** as a sufficient explanation; a timing race where CEF initialized before the service was started remained plausible, not proven. Existing helper started after a renderable X11 window first mapped.

**Source review:** Pinned Winlator upstream SHA `8077f374ef2d54127b088de9e8cd7b4af14d9c8b`, `XServerDisplayActivity.setupXEnvironment`: constructs `wine explorer /desktop=..., C:\\windows\\winhandler.exe /dir ...` guest command. `GuestProgramLauncherComponent.start` runs through rootFS Box64. Previous `startCharoiteBattleNetMonitor()` waits until first mapped window and WinHandler socket readiness; it is too late to guarantee RPC during client initialization. `ProcessHelper.exec` uses command argument splitting rather than shell, so a naive shell `&&` wrapper cannot safely be appended.

**Implemented directly in GitHub `main`, no branch changes:**
- `0a9b4b2bd9a4cd7b4cc5ace26b0ff74f1846add7`: first-party 32-bit Wine guest helper gains separate **`/preflight-launch`** mode, generating fixed-format numeric `C:\\CharoitePortal\\Diagnostics\\charoite_bnet_rpc_preflight.txt`. It calls existing `try_start_rpc_service`, requires RPC RUNNING and verified original Disabled startup type rollback, and only then uses **Win32 `CreateProcessW`** to spawn the original `C:\\windows\\winhandler.exe` with its original `/dir`, installed Battle.net executable/arguments. No batch/shell or credentials/log copying. It refuses to launch the client if service/rollback fails, reports `preflight_rpc_ready`, `preflight_client_spawn_attempted`, `preflight_client_spawn_error`, `preflight_launch_ready`, and waits while WinHandler runs. Native helper still supports ordinary read-only `/monitor`.
- `6468634375ad0fe7ba5726bffea14afead7d8d15`: `CharoiteGameSessions` adds `charoite_bnet_rpc_preflight` Intent flag *only* for the already consented Battle.net RPC startup experiment, excluding installers, other environments, and arbitrary games.
- `4afd3222303708e85c56f7984d9dc8bd3fffae96`: `runtime-preview/overlay.py` patches upstream guest-executable setup. With the scoped flag it copies the helper to the **selected Battle.net container** before starting Wine and launches **`wine explorer ... C:\\CharoitePortal\\Diagnostics\\charoite_bnet_network_probe.exe /preflight-launch ...`** as the FIRST Win32 program instead of WinHandler; helper starts RPC, restores Disabled setting, launches WinHandler. For the explicit preflight path the old after-window live monitor now uses **read-only `/monitor`**, not a second startup attempt. On helper preparation/prefix mismatch, fall back to normal launch with `RPC_PREFLIGHT_PREPARE_FAILED` or `RPC_PREFLIGHT_PREFIX_MISMATCH` Android marker; do not treat absent preflight report as proof of timing success.
- `f37b27b4e8bdf44685488644521abb72fe192fc7`, `19db4c76e3f7e1fb2e8128ba28a33d62ba8f3d18`, `294f63667c5c8570521bf3b717cba58e35e1298f`: `CharoiteBattleNetSupport.inspectGuestRpcPreflight` reads only numeric Charoite fields from the dedicated preflight report with timestamp and concise before-client interpretation. It is appended to **VIEW LIVE AGENT MONITOR** and therefore also appears in **VIEW BATTLE.NET LOGIN / CEF REPORT**. No sensitive Blizzard data.
- `27402551195b34f0cfa3e4a80f42b6ba3c7398fa`: new `runtime-preview/tests/test_battlenet_rpc_preflight_contract.py` covering realm and consent scoping, launch-order hook, CreateProcess gating, required rollback and numeric-only report. `38484cf948bfa91c7887ffd0359a094a3f639bc0` updates stale read-only service regression after changing C helper return type. Intermediate CI failed stale test assertions, corrected in final code.
- **Verified final build:** GitHub Actions **40591365458** SUCCESS; source SHA **`294f63667c5c8570521bf3b717cba58e35e1298f`**; `Charoite-Portal-Android-APK` artifact ID **12773863471**, compressed 231,426,060 bytes. **130 Python contract tests PASS**, full Android APK and Win32 tool compiled. No on-device validation of this prelaunch path yet.

**Precise next user phone test:**
1. Update `com.charoite` from successful run https://github.com/rgarn023/CharoitePortal/actions/runs/40591365458 without uninstall or data clearing.
2. Close previously running Battle.net session; choose **Battle.net Gaming → Setup → TRY BATTLE.NET (START WINE RPC SERVICE)** and confirm. The same button now tests BEFORE-client RPC startup instead of post-first-window startup.
3. Observe the actual Windows UI. If launcher fails to appear, that is useful evidence that gate did not complete; do not keep restarting or deleting prefix.
4. After ~30 seconds return to Portal → **VIEW BATTLE.NET LOGIN / CEF REPORT** → **Copy report**; new lower section **BATTLE.NET BEFORE-CLIENT RPC PREFLIGHT** reports `preflight_attempted`, `preflight_before_client`, `preflight_rpc_ready`, `preflight_client_spawn_error`, `preflight_launch_ready`, start type, service START/RUNNING and rollback status; regular live monitor and CEF logs still included.
5. **If** `preflight_rpc_ready=1`, `preflight_launch_ready=1`, `RpcSs RUNNING` but spinner persists, abandon service timing as primary explanation and investigate CEF renderer flags/graphics backend or Agent IPC further, with bounded useful log categories and rollback of experiments. If preflight fails/no report, debug launched guest executable and WinHandler handoff. Do not claim Diablo III/IV works.

## 16. October 27, 2026 — Final diagnostics safeguard and APK build verification

The initial before-client RPC experiment at code SHA `294f63667c5c8570521bf3b717cba58e35e1298f` passed 130 CI tests and was published in successful Actions run `40591365458`. Review caught an important failure-case gap: if the preflight refuses to start the Windows client, then the usual post-first-window Live Agent Monitor is absent, and the Portal's early-return branch would have hidden the preflight file despite it being available.

**Fixed before delivery:**
- Commit `a46710312fdceecf2f4bcb5eb31188f180247eb2`: `CharoiteBattleNetSupport.inspectInSessionAgentMonitor()` now appends `inspectGuestRpcPreflight(root)` even on the **no live monitor report** return path. Thus the exact RPC/rollback/CreateProcess result is visible under **VIEW BATTLE.NET LOGIN / CEF REPORT**, whether or not Battle.net opens any window.
- Commit `d1b10879dd6c3d64b931fb7fd15c983d0dc2cff9`: strengthened `test_battlenet_rpc_preflight_contract.py` for the early-return behavior.
- **Current final successful APK:** GitHub Actions run **40591957435**, source SHA **`d1b10879dd6c3d64b931fb7fd15c983d0dc2cff9`**, `Charoite-Portal-Android-APK` artifact ID **12774297702** (231,424,506 byte ZIP, uploaded, nonexpired). Regression suite, native Win32 compile, full Android app build and signing succeeded. **On-device preflight has not been checked yet**.
- The APK source commit differs from any subsequent `[skip ci]` handoff-only commit, which does not rebuild. Existing `com.charoite` private data and other environment behaviors remain unchanged.

**Next phone action:** With prior Battle.net Wine session closed, update the APK without uninstalling/clearing app data, run **Battle.net Gaming → Setup → TRY BATTLE.NET (START WINE RPC SERVICE)** (confirm), wait about 30 seconds, and copy **VIEW BATTLE.NET LOGIN / CEF REPORT**. Focus on `BATTLE.NET BEFORE-CLIENT RPC PREFLIGHT`: `preflight_rpc_ready`, `preflight_client_spawn_attempted`, `preflight_client_spawn_error`, `preflight_launch_ready` plus `monitor_rpc_restore_confirmed`. Compare spinner/login and later live monitor. If `preflight_launch_ready=1` and login still spins, don't keep restarting RPC; focus on CEF renderer/GPU process and Agent IPC. If no preflight report, inspect startup state/missing helper. Do not assume success based on Android CI alone.

## 17. October 27, 2026 — Before-client RPC preflight VERIFIED on device; focused CEF/Agent diagnostics built

**New actual user phone report at 22:29 EDT** after installing previous build from GitHub Actions run `40591957435`:
- `preflight_attempted=1`, `preflight_before_client=1`, `preflight_rpc_ready=1`, `preflight_client_spawn_attempted=1`, `preflight_client_spawn_error=0`, `preflight_launch_ready=1`. This means Charoite started RPC and restored original configuration **BEFORE** the Windows client process was spawned.
- `monitor_rpc_start_before_type=4`, `monitor_rpc_temporary_enable_attempted=1`, `monitor_rpc_start_win32_error=0`, `monitor_rpc_start_after_state=4`, `monitor_rpc_restore_attempted=1`, `monitor_rpc_restore_error=0`, `monitor_rpc_restore_confirmed=1`, `monitor_rpc_start_type_after=4`, `monitor_rpc_recovery_error=0`.
- Post-launch process sample: `monitor_rpc_service_running_samples=16`, `monitor_rpcss_present_samples=16`, `monitor_agent_present_samples=15`, `monitor_client_present_samples=16`, `monitor_max_client=5`, no enumeration or SCM query errors. This independently confirms RPC remained healthy throughout sample.
- Browser acceleration still OFF in 1 configuration. Six client logs contain 62 error-like lines with 20 rendering refs, 8 GPU/compositor refs, 5 GPU-process refs, 3 CEF refs, 3 Agent/IPC refs, 6 network refs, 3 login/auth refs, 0 counted crashes. These counts overlap and include possibly historic entries.
- **Unresolved UX:** This message only supplied diagnostics; do NOT claim Battle.net reached login or remained spinning THIS time. Earlier user explicitly stated it continued spinning when RpcSs was started AFTER first window; now startup timing has been corrected and verified. Request exact UI outcome together with new report.

**Current niche compatibility references checked:** Lutris Battle.Net troubleshooting `docs/Battle.Net.md` explicitly associates **spinning icon, no login buttons** with CEF browser hardware acceleration and stale cache, separately from Agent errors. User's saved acceleration is already OFF. WineHQ 2026 reports note Battle.net startup/CEF behavior is sensitive to Wine/Staging versions; do not assume replacing the entire runner fixes it. Historical Blizzard Agent logs in a public forum describe local port 1120, but Agent version/port can change. Links: https://github.com/lutris/docs/blob/master/Battle.Net.md and https://us.forums.blizzard.com/en/blizzard/t/last-update-completely-breaks-wine-compatibility/33122 . Do not use these as proof of an actual Agent port on Galaxy.

**New code directly committed on existing `main`:**
- `7338295138dd7afabe060f1763fef0a4461748cc` — Win32 guest diagnostic `runtime-preview/charoite-core/diagnostics/charoite_bnet_network_probe.c` now counts **Battle.net.exe parent-child process relationships** using ToolHelp PID data only (no commands, tokens, memory, window titles), recording `monitor_max_client_children` and `monitor_client_child_present_samples`. Also tests **TCP connect ONLY** to `127.0.0.1:1120` on 4 of 16 monitor samples, nonblocking 200 ms per probe, logs only `monitor_agent_loopback_1120_tests`, `monitor_agent_loopback_1120_connect_success`, `monitor_agent_loopback_1120_last_winsock_error`. Does not send HTTP, read traffic, or modify Blizzard files. That port was used by an older Agent, but modern builds may differ, so no response is NOT proof of IPC failure. No client crash or login conclusion from parent-child count alone.
- `d6a794939e97deb247c4cd1245c0376c5f806ab5` — `CharoiteBattleNetSupport.java` interprets these numeric fields with limitations, adds focused text categories (**empty login URL**, **browser/CEF subprocess exits**, **TLS/certificate failures**) from bounded client log tails, and notes how many of 6 sampled files were modified since saved preflight timestamp; warns even recently modified files can contain older entries. No raw logs, account IDs, tokens, URLs or credentials exposed.
- `838b3facbe97569949e361afa9cee2c1394b844f`, `0bb75f1bbcfbecd1708e471814080e13ff5cfcd3`, `4d006f1d769b32dedda7bceef596177135164e34` — new `runtime-preview/tests/test_battlenet_cef_agent_ipc_contract.py` and its scoping correction, protect no-HTTP *local* Agent probe while allowing the existing standalone public network probe. An earlier CI failed a test falsely checking the entire Windows helper rather than only the local socket function; final tests pass.

**Final verified APK:** GitHub Actions run https://github.com/rgarn023/CharoitePortal/actions/runs/40621810208 **SUCCESS**, code SHA `4d006f1d769b32dedda7bceef596177135164e34`, `Charoite-Portal-Android-APK` artifact **12787088516** compressed **231,401,093 bytes**, unexpired. **133 Python regression tests passed**, Win32 native diagnostic and Android APK successfully compiled and signed. Handoff docs-only commit uses `[skip ci]`, so may be newer than APK code SHA. NO on-device test yet of this newest focused Agent/CEF diagnostic.

**Next user/device test:** Update existing `com.charoite` APK without uninstalling or clearing data; close old Battle.net session; launch the same **Battle.net Gaming → Setup → TRY BATTLE.NET (START WINE RPC SERVICE)**. Allow ~30 seconds, then go to **VIEW BATTLE.NET LOGIN / CEF REPORT** → Copy. Look for `preflight_rpc_ready=1`, `preflight_launch_ready=1`, the new child process and historical Agent localhost 1120 counts, new CEF error signatures, and actual login window/spinner observation. If local port is closed, *do not* conclude Agent is broken (port not guaranteed). If child process count high or CEF error signatures appear, consider focused Wine/Staging CEF compatibility measures. If still spinning, existing **BACK UP + RESET BATTLE.NET BROWSER CACHE** is an optional user-approved reversible cache-folder rename; close Battle.net first, keep Agent and game data untouched. Do not automatically delete `ProgramData/Battle.net`, reset the entire prefix, upgrade Wine or uninstall games.

## 18. October 27, 2026 — Historical Agent port 1120 refused; new owner-scoped TCP listener diagnostic built

**User's actual 22:41 EDT Galaxy findings using APK run `40621810208`:**
```
preflight_rpc_ready=1
preflight_client_spawn_error=0
preflight_launch_ready=1
monitor_rpc_start_after_state=4
monitor_rpc_restore_confirmed=1
monitor_rpc_service_running_samples=16
monitor_agent_present_samples=15
monitor_client_present_samples=16
monitor_max_client_children=4
monitor_client_child_present_samples=13
monitor_agent_loopback_1120_tests=4
monitor_agent_loopback_1120_connect_success=0
monitor_agent_loopback_1120_last_winsock_error=10061
```
WinSock `10061` is **connection refused** at `127.0.0.1:1120`. It does NOT prove that the Agent IPC transport fails: the port was only historically documented and may be obsolete. `Agent.exe` lives in the Wine session; four Battle.net child processes were present, but process ancestry alone cannot identify which are Chromium browser/GPU helpers. One browser config reports acceleration OFF. Logs: 6 files (2 modified since preflight), 62 error-like lines, 20 rendering refs, 8 GPU/compositor, 5 GPU-process, 3 CEF, 3 Agent/IPC, 6 network, 3 login/auth; zero narrow CEF subprocess exits, empty login URL, certificate errors, or counted crashes. Counts may overlap or include older content. User has not expressly confirmed UI outcome for this *latest* launch; earlier reported spinner.

**Public technical verification:** Microsoft's `GetExtendedTcpTable` supports `TCP_TABLE_OWNER_PID_LISTENER` for IPv4, and the pinned Wine 10.10 source contains the implementation. This is a read-only way to discover listener ownership without guessing a port. https://learn.microsoft.com/en-us/windows/win32/api/iphlpapi/nf-iphlpapi-getextendedtcptable . `lutris/docs/Battle.Net.md` describes spinning login symptoms and optionally resetting browser caches after acceleration is disabled; do not delete Blizzard data automatically. https://github.com/lutris/docs/blob/master/Battle.Net.md

**Real GitHub `main` changes:**
- `c806cdc65a3f9f63e5e47b4be9514e50c184a6a4` updates `runtime-preview/charoite-core/diagnostics/charoite_bnet_network_probe.c`. Keeps *in-memory only* up to 16 PIDs for `Agent.exe` observed through ToolHelp; on the 4 existing staggered samples calls `GetExtendedTcpTable` `TCP_TABLE_OWNER_PID_LISTENER` (IPv4) with a bounded 512 KiB table, counts only `LISTEN` rows with PID matching Agent and counts loopback/wildcard owned listeners. Outputs `monitor_agent_tcp_ipv4_owner_queries`, `monitor_agent_tcp_ipv4_owner_query_success`, `monitor_agent_tcp_ipv4_listener_present_samples`, `monitor_agent_tcp_ipv4_max_listeners`, `monitor_agent_tcp_ipv4_max_loopback_listeners`, `monitor_agent_tcp_ipv4_example_loopback_port`, and `monitor_agent_tcp_ipv4_last_query_error`. No port scanning, arbitrary process information, IP addresses, commands, credentials or packet data, and no new connects to discovered ports. **If count=0 or error, may reflect Wine API limitations, named pipes, Unix sockets or IPv6—not proof of Agent failure.**
- `647e2390727e9763650539f050c7d6d482bde8ef` links `-liphlpapi` in `.github/workflows/runtime-preview.yml` for 32-bit native helper.
- `5a30f2f64ac0f382696eb8424b8681262ef47858` extends the read-only `CharoiteBattleNetSupport.inspectInSessionAgentMonitor()` output, including a clear warning against over-interpreting missing IPv4 owned listeners.
- `6ec4310caa2b35eccdaf094e465121450e70bdf5` strengthens `runtime-preview/tests/test_battlenet_cef_agent_ipc_contract.py` for owner-PID matching, privacy, bounded queries, linking and report wording.
- **Successful verified APK build:** GitHub Actions `40622918379`, source SHA **`6ec4310caa2b35eccdaf094e465121450e70bdf5`**, artifact `Charoite-Portal-Android-APK` ID **12788137725**, 231,401,681-byte compressed archive, uploaded/not expired. **134 regression tests PASS**, native and Android builds/signing PASS. No on-device validation of the latest listener query yet.

**Next phone test:** Install APK over existing `com.charoite` (never uninstall/clear app data). Close old Battle.net session and launch via **Battle.net Gaming → Setup → TRY BATTLE.NET (START WINE RPC SERVICE)**, then copy **VIEW BATTLE.NET LOGIN / CEF REPORT** after ~30 sec. Focus on new `monitor_agent_tcp_ipv4_* ` fields, old port 1120 results, `preflight_rpc_ready`/`preflight_launch_ready`, and whether login appears. If the spinner persists, consider the already implemented **BACK UP + RESET BATTLE.NET BROWSER CACHE** opt-in control with cleanly closed client (renames selected cache folders to backups; preserve Agent, games and account settings), then compare outcomes rather than blindly changing Wine. Prioritize controlled CEF/IPC diagnostics over broad destructive resets.

## 19. October 27, 2026 — Actual Agent-owned local listener discovered; passive client→Agent TCP correlation built

**New real device report at 23:00 EDT, using successful prior APK `40622918379`:**
- `monitor_agent_tcp_ipv4_owner_queries=4`, `monitor_agent_tcp_ipv4_owner_query_success=4`, `monitor_agent_tcp_ipv4_listener_present_samples=4`, `monitor_agent_tcp_ipv4_max_listeners=1`, `monitor_agent_tcp_ipv4_max_loopback_listeners=1`, `monitor_agent_tcp_ipv4_example_loopback_port=38789`, `monitor_agent_tcp_ipv4_last_query_error=0`. This verifies `Agent.exe` owns a local IPv4 listener, not necessarily stable at 38789 throughout all samples or across sessions.
- Historical hard-coded `127.0.0.1:1120`: `monitor_agent_loopback_1120_tests=4`, `monitor_agent_loopback_1120_connect_success=0`, `monitor_agent_loopback_1120_last_winsock_error=10061` (connection refused). **Do NOT infer Agent IPC is broken**, since Agent listens elsewhere; port changes may be dynamic.
- `preflight_rpc_ready=1`, `preflight_launch_ready=1`, before-client `monitor_rpc_start_after_state=4`, `monitor_rpc_restore_confirmed=1`, `monitor_rpc_service_running_samples=16`, `monitor_agent_present_samples=15`, `monitor_client_present_samples=16`, `monitor_max_client_children=4`, `monitor_client_child_present_samples=14`.
- Existing browser acceleration OFF. Six most recent sampled client logs: 79 error-like entries, 32 rendering, 11 GPU/compositor, 8 GPU-process, 2 CEF, 2 Agent/IPC, 6 network, 2 login/auth, zero matches for device-lost, CEF subprocess exit, empty login URL, TLS/certificate, or crash. These overlap and may include historic lines.
- User did not explicitly state latest UI outcome (spinner vs login) in this report; don't assume.

**Implementation completed directly on GitHub `main`:**
- `1354134201b23a91d64de00f214d2174a50343b7`: `runtime-preview/charoite-core/diagnostics/charoite_bnet_network_probe.c` keeps up to 64 observed `Battle.net.exe`/launcher PIDs and 16 `Agent.exe` PIDs only in memory, retaining original passive ToolHelp. A separate bounded (max 512 KiB), **read-only** `GetExtendedTcpTable(AF_INET,TCP_TABLE_OWNER_PID_ALL)` query runs during each of the 4 existing staggered monitoring checks. For each snapshot it collects Agent-owned loopback/wildcard LISTEN ports in memory, counts `MIB_TCP_STATE_ESTAB` connections owned by Agent and Battle.net, and checks whether a Battle.net-owned ESTABLISHED TCP row has loopback remote port matching an Agent listener seen in the **same snapshot**. Reports aggregate numeric-only fields: `monitor_agent_ipc_tcp_connection_queries`, `monitor_agent_ipc_tcp_connection_query_success`, `monitor_agent_ipc_tcp_agent_established_max`, `monitor_agent_ipc_tcp_client_established_max`, `monitor_agent_ipc_tcp_client_to_agent_present_samples`, `monitor_agent_ipc_tcp_client_to_agent_max`, `monitor_agent_ipc_tcp_last_query_error`. Does NOT connect/send/recv, log PIDs/addresses/credentials/payload or alter Wine/Blizzard. A positive match indicates matching TCP socket state, **not** successful login or complete application IPC. Zero may mean short-lived HTTP, IPv6, named pipes, other IPC, or Wine incomplete tracking.
- `af8ed9bcf775ac5341210e4d37e6c107db277c53`: CharoiteBattleNetSupport Java report interprets counts and explicitly warns on zero or incomplete tests. `b8d0ddcc0e19021f6efccdf6ce24d3e586e43bb1`: new static regression protecting PID scoping, read-only TCP table use, bounding and safe reporting.
- Official Windows `GetExtendedTcpTable` docs list `TCP_TABLE_OWNER_PID_ALL` and `MIB_TCPTABLE_OWNER_PID` for IPv4, and Microsoft documents owning PID and TCP connection state: https://learn.microsoft.com/en-us/windows/win32/api/iphlpapi/nf-iphlpapi-getextendedtcptable and https://learn.microsoft.com/en-us/windows/win32/api/tcpmib/ns-tcpmib-mib_tcprow_owner_pid
- **Verified new APK:** https://github.com/rgarn023/CharoitePortal/actions/runs/40624809048 GitHub Actions SUCCESS, code SHA `b8d0ddcc0e19021f6efccdf6ce24d3e586e43bb1`, artifact `Charoite-Portal-Android-APK` ID **12788843142**, ZIP 231,430,397 bytes, not expired. **135 regression tests passed**, Android and Win32 builds/signing success. This handoff commit uses `[skip ci]` and is newer than code; app not yet on-device tested.

**Phone test:** Update `com.charoite` in-place (never uninstall or clear app storage), close older Battle.net Wine session, select Battle.net Gaming → Setup → **TRY BATTLE.NET (START WINE RPC SERVICE)**, confirm, allow ~30 seconds, return and copy **VIEW BATTLE.NET LOGIN / CEF REPORT**. Focus on `monitor_agent_ipc_tcp_connection_query_success`, `monitor_agent_ipc_tcp_client_to_agent_present_samples`, `monitor_agent_ipc_tcp_client_to_agent_max`, `monitor_agent_ipc_tcp_last_query_error` and the actual Battle.net UI. If listener is present and client socket correlation is zero across samples, do not assert IPC failure; can try reversible optional browser cache reset after fully closing client, then test again. Preserve Agent/game files and existing Wine prefixes.

## 20. October 27, 2026 — No sampled Battle.net→Agent IPv4 match; combined RpcSs + CEF graphics experiment built

**New actual user Galaxy report at 23:31 EDT using previous successful APK `40624809048`:**
- `preflight_rpc_ready=1`, `preflight_client_spawn_error=0`, `preflight_launch_ready=1`; RpcSs RUNNING **16/16**, startup setting restored original Disabled (`monitor_rpc_restore_confirmed=1`), no Win32 errors.
- `monitor_agent_present_samples=15`, `monitor_max_agent=2`, `monitor_client_present_samples=16`, `monitor_max_client=5`, four child processes maximum, child processes in 14 samples.
- Agent-owned IPv4 listening table: four queries succeeded; Agent-owned LISTEN in four samples; maximum one local loopback/wildcard listener, example port **38789**. This port is an example (not proven stable or fixed).
- TCP owner correlation four queries succeeded: `monitor_agent_ipc_tcp_agent_established_max=8`, `monitor_agent_ipc_tcp_client_established_max=14`, `monitor_agent_ipc_tcp_client_to_agent_present_samples=0`, `monitor_agent_ipc_tcp_client_to_agent_max=0`, error 0. **No matching direct client socket was seen in 4 spaced snapshots**, but both processes have other established TCP sockets. Zero does not prove broken Agent IPC; short-lived local connections, named pipes, IPv6 or other transports may be missed. Earlier hard-coded port 1120 remains refused (WSA 10061), not a meaningful Agent test.
- Browser acceleration config OFF. 6 sampled log files with 89 error-like lines, 40 rendering, 13 GPU/compositor, 10 GPU-process, 1 CEF, 1 Agent/IPC, 6 network, 1 login/auth; no counted CEF-subprocess exit, empty login URL, TLS/certificate, device lost, crash. Overlapping categorization and possibly old log lines, not definitive root cause.
- The user's latest message is **only diagnostics**. The user has not explicitly stated whether the visible spinner persisted in *that* trial. Do not claim login succeeded, nor that a combined graphics experiment has fixed it.

**Decision and code:** Existing Battle.net buttons offered an RPC preflight with normal graphics and a separate compatibility graphics mode **without RPC preflight**. Therefore, couldn't isolate CEF/graphics with the already-proven working RPC service *simultaneously*. Rather than destructive Wine changes or endless Agent port probes, implement one **explicitly consented combined test** with existing per-session compatibility renderer.
- Commit `3892d26a7b738b5b05929ceacb71ffcc351c0481` and string correction `29697438cdb575a428ef699cdbfb752600a5d8dc` modify only `runtime-preview/TouhouEntryActivity.java`. Inside already-existing **TRY BATTLE.NET (START WINE RPC SERVICE)** confirmation add neutral **RPC + graphics** alongside positive **Try once** and negative **Cancel**. New shared `launchBattleNetRpcTest(boolean compatibilityGraphics)` reuses CharoiteGameSessions.launch with `agentCompatibility=compatibilityGraphics`, `disableBattleNetBrowserGpu=true`, `inProcessBrowserGpu=false`, `tryStartBattleNetRpc=true`. Existing runtime `overlay.py` already supports VirGL + WineD3D session graphics backend for the compatibility flag and switches `WINEESYNC=0`, `WINEFSYNC=0`, emits Wine debug warnings and uses a session-local browser `--disable-gpu` flag. Existing source `CharoiteGameSessions.java` scopes these to **the active Battle.net environment and installed Battle.net exe, NOT installers/other games**; before-client RPC service gate and config rollback unchanged.
- Updated explanatory text so UI no longer incorrectly says RpcSs is currently stopped. New option changes neither saved realm settings nor files and carries the same recovery-marker safety. Graphics experiment may have no effect or fail rendering on the device; original Try once unaffected.
- Commits `7268e3723210787129c0774f240c5f916cfc9062`, `61c8d1156fe9e5ba8443afd82f4a6009845896ee`: update regressions to verify both explicit options, direct installed-client launch, no data deletion, scope/consent and unchanged preflight. Earlier intermediate builds failed stale test expectations because method was refactored; final build is passing.
- **Verified final GitHub Actions APK:** https://github.com/rgarn023/CharoitePortal/actions/runs/40627760121 — SUCCESS, source SHA **`61c8d1156fe9e5ba8443afd82f4a6009845896ee`**, `Charoite-Portal-Android-APK` artifact **12789983316**, ZIP **231,430,612 bytes**, nonexpired. **135 regression tests passed** in final Actions job; native helper, full signed Android APK and artifact upload completed. No actual on-device test of combined mode yet. Documentation-only commit `[skip ci]` doesn't invalidate APK.

**Next exact phone test:** Update existing app `com.charoite` in-place, without uninstall/clearing data; close old Battle.net Wine session; Battle.net Gaming → Setup → **TRY BATTLE.NET (START WINE RPC SERVICE)** → choose the new **RPC + graphics** option, not **Try once**; observe actual UI; wait around 30sec and copy **VIEW BATTLE.NET LOGIN / CEF REPORT**. A changed renderer alone doesn't prove a fix. A failed/blank window warrants returning to ordinary Try once; do not delete Agent or games. If spinner persists even with combined preflight+WineD3D/VirGL, optional user-approved **BACK UP + RESET BATTLE.NET BROWSER CACHE** is the next reversible test (requires Battle.net closed). Then investigate precise Chromium failure and/or IPC without automatic upgrades or prefix deletion.

## 21. October 28, 2026 — Galaxy RPC + graphics-era diagnostic; do not infer CEF success from category totals

**New pasted phone report, Wed Oct 28 at 00:13 EDT, after APK code `61c8d1156fe9e5ba8443afd82f4a6009845896ee` / GitHub Actions `40627760121`:**
- Same-session monitor completed all 16 samples. Agent present in 15, max Agent count=1. Client present in 16, max client count=5, up to 4 child processes observed (13 sample appearances). All 16 RPC status queries reported service RUNNING; service startup type was originally Disabled, temporarily set Manual, then rollback confirmed `monitor_rpc_restore_confirmed=1` and recovery error 0. `preflight_rpc_ready=1`, `preflight_launch_ready=1`, client-spawn error 0. RPC repair and prelaunch logic continue to behave correctly.
- 4/4 Agent TCP listener owner queries succeeded, showed 1 Agent-owned IPv4 local listener in all four samples; *example* port `38789` (not proof the same port at every sample). 4/4 IPv4 connection owner queries succeeded: `monitor_agent_ipc_tcp_agent_established_max=5`, `monitor_agent_ipc_tcp_client_established_max=10`; **`monitor_agent_ipc_tcp_client_to_agent_present_samples=0`**, `max=0`, no query errors. This means no directly matched client-to-Agent IPv4 localhost TCP rows were observed in four spaced snapshots, **not** proven broken IPC.
- Browser acceleration OFF in the one configured settings file. Client 6-log sample: 2 files modified since preflight; 83 error-like lines, 24 rendering references, 8 GPU/compositor, 6 GPU-process, 3 Agent/IPC, 4 network, 1 crash/exception, 1 CEF, 1 login/auth. Zero narrow subprocess-exit, blank login URL, or TLS errors. Category counts are overlapping, often historical; the new single crash reference is NOT proof of a new crash.
- Critically, **these diagnostics do not identify if the user selected the new `RPC + graphics` dialog option rather than baseline `Try once`**, and the user did not describe visible UI (still spinning vs login reached). Do not claim the new combined renderer works or fails from the counts alone.
- Existing `BACK UP + RESET BATTLE.NET BROWSER CACHE` action in `runtime-preview/charoite-core/CharoiteBattleNetSupport.java` only moves `users/*/AppData/Local/Battle.net/{Cache,BrowserCaches,GPUCache,Code Cache}` to timestamped `.charoite-backup-` folders on same filesystem. It requires explicit confirmation and *user fully closes Battle.net first*. It does **not** move or delete `ProgramData/Battle.net`, `Agent.exe`, installed games/saves or saved settings. Never auto-run reset or delete the parent ProgramData folder.
- Reviewed current Lutris troubleshooting source: https://github.com/lutris/docs/blob/master/Battle.Net.md mentions spinning icon/no login buttons and recommends disabling acceleration or clearing cache; it also mentions `drive_c/ProgramData` but that directory can contain installed Blizzard Agent and configuration. For Charoite, our narrower backed-up browser cache action should be the first safe reversible test. The saved browser acceleration is already OFF. WineHQ 2026 reports that Wine/staging version and CEF are relevant but do not justify updating all Wine in the user's prefix without controlled evidence.
- **No new source code/APK required for this report**. Latest verified APK remains GitHub Actions `40627760121`, artifact `12789983316`, 135 passing regression tests. The handoff is updated via `[skip ci]` documentation-only commit.

**Next response/request:** Ask briefly which button was selected (RPC + graphics or Try once) and whether still spinning; if still spinning after confirmed combined mode, have user *close all Battle.net and Agent processes*, choose already available **BACK UP + RESET BATTLE.NET BROWSER CACHE** with explicit confirmation, then try again. If further debugging required after this, instrument a **mode-specific launch fingerprint** in a future APK so logs can distinguish actual launch flags and whether renderer changed, rather than comparing overlapping historical log-category counts. Prefer minimal changes, not another speculative Agent or RPC manipulation.

## 22. October 28, 2026 — User confirms spinner persists; numeric launch-mode fingerprint implemented and built

**Current real user outcome:** After uploading report from Wed Oct 28 00:13 EDT (successful prior APK `40627760121`), user replied **"Still spinning"**. Do not assume which option (**Try once** vs **RPC + graphics**) they selected in the preceding dialog; previous logs had NO mode marker. This is a user-confirmed visual failure to reach login, despite RPC and running Agent. Do not claim the system is fixed.

**New actual changes committed directly to current `rgarn023/CharoitePortal` main:**
- `a28d77dcab4f75052dbaa3e1c19d4fdfd32d903b` adds numeric-only Android diagnostic `recordBattleNetLaunchCommand`, `recordBattleNetRuntimeEnv`, `inspectBattleNetLaunchFingerprint` in `runtime-preview/charoite-core/CharoiteBattleNetSupport.java`. Writes only Charoite-owned `C:/CharoitePortal/Diagnostics/charoite_bnet_launch_command.txt` and `charoite_bnet_launch_env.txt`, stamps time, reads with strict numeric booleans. Detects stale (>1h) and desynchronized (>10 seconds) snapshots. Does not read/write Blizzard registry, account data, command args, paths or Agent files.
- `088a25250fe825460170af61722373a0856da31e` instruments `runtime-preview/overlay.py` in two EXISTING upstream anchors (no replacement of Wine): when assembled `getWineStartCommand()` is available, capture **actual presence** of `--disable-gpu` and resolved renderer `GraphicsDrivers.VIRGL`, `DXWrappers.WINED3D` versus requested Intent flags. Later, after Wine EnvVars are built but before they are passed to the guest launcher, record actual effective `WINEESYNC=0`, `WINEFSYNC=0` and `locationapi=` override presence as numeric booleans. Strictly scoped to active Battle.net environment installed-client monitor. No raw flags/command line in report.
- `bd7ae5c1f3617f40305df2701884d5db88a3f870` adds **BATTLE.NET LAUNCH FINGERPRINT** to full **VIEW BATTLE.NET LOGIN / CEF REPORT** and standalone live monitor, including early/no-Wine-monitor case. Explanation explicitly says these are Android selections, not proof Chromium honored the flags or login succeeded.
- `553d9cbd8dc49edc84016fda2adc83cb27c031b5` creates `runtime-preview/tests/test_battlenet_launch_fingerprint_contract.py`, covering scoped flags, real renderer/EnvVar introspection, safe numeric-only Charoite files, old/mixed snapshot warnings, and report presence. **138 regression tests passed**.
- **Verified latest APK:** Actions **https://github.com/rgarn023/CharoitePortal/actions/runs/40641148611** SUCCESS. Actual source SHA `553d9cbd8dc49edc84016fda2adc83cb27c031b5`. Signed `Charoite-Portal-Android-APK` artifact **12795777267**, ZIP 231,433,090 bytes, nonexpired. Win32 diagnostics compilation and signed Android build PASS. This documentation `[skip ci]` commit will be newer than APK source.
- **No on-device test yet** of new launch fingerprint, graphics selected-mode verification or browser cache reset. Existing saved browser acceleration OFF. Old RPC startup and safe restoration remain correct and unchanged.

**Next phone steps:** Update `com.charoite` APK **over** installed app, never uninstall/clear storage. Fully close Wine Battle.net session. Recommended reversible current control: Battle.net Gaming → Setup → **BACK UP + RESET BATTLE.NET BROWSER CACHE** after client is closed; this prompts confirmation then only moves selected `AppData/Local/Battle.net/{Cache,BrowserCaches,GPUCache,Code Cache}` to timestamped backups on same filesystem, not `ProgramData/Battle.net`, Agent, games or registry. Then launch **TRY BATTLE.NET (START WINE RPC SERVICE) → RPC + graphics** and after ~30sec copy **VIEW BATTLE.NET LOGIN / CEF REPORT**. Check `launch_compatibility_requested=1`, `launch_disable_gpu_command_present=1`, `launch_renderer_virgl_resolved=1`, `launch_dxwrapper_wined3d_resolved=1`, `launch_env_esync_off=1`, `launch_env_fsync_off=1`. A 0 identifies launch plumbing gap; values=1 only proves selection/command, NOT successful CEF rendering. Also note whether login appears or spinner persists. If they already reset cache, don't repeat; ask for new fingerprint. Do not jump to a full Wine rewrite or destructive Blizzard data removal.

---
**End of current Charoite Portal handoff.**
