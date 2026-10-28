# CHAROITE PORTAL / CHAROITE CORE — CURRENT PROJECT HANDOFF

**Current handoff updated:** October 28, 2026  
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

**Current priority (October 28; new feasibility direction):** User confirms Battle.net **STILL SPINS** despite verified RpcSs preflight/rollback, Agent running/listening and both plain and combined graphics trials. Do not keep restarting RPC or invent an unverified fix. New independent *working Android reference* discovered: https://github.com/ashmerra/wehavephones . This Winlator-derived project explicitly reports Battle.net login/sign-in and WoW Classic Era **in-world gameplay on a Samsung Galaxy S26 Ultra** (https://github.com/ashmerra/wehavephones/blob/main/docs/TESTED_DEVICES.md and https://github.com/ashmerra/wehavephones/issues/18). It uses **GE-Proton 10.0-34 ARM64EC**, an ARM64-specific ntdll/wineserver patch, FEX, specific Chromium flags `--disable-gpu --enable-features=NetworkServiceInProcess2` and device graphics profiles: https://github.com/ashmerra/wehavephones/blob/main/docs/WEHAVEPHONES_RUNTIME.md . Evidence supports feasibility of Battle.net on this phone, **not** that existing Charoite's bundled Wine/Box64 setup can support it unchanged, nor that Diablo IV is playable. Strategic next step: evaluate integration of an optional **separate Battle.net runtime backend** as a cleanly isolated engine/environment, preserving current Charoite Core + TPDP/Touhou Wine prefixes. Check license/build artifacts and test in a NEW prefix first; do not replace shared Wine silently, run destructive cache deletes, or migrate existing saves. Existing browser cache backup/reset remains available as a reversible user-approved check, but the larger issue may require engine updates. Do not claim completion, APK, or new runtime installed; no code change has implemented this plan yet.

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

## 23. October 28, 2026 — Battle.net still spins; independent proof of Android/S26 feasibility changes strategy

The user answered **"Still spinning"**, then asked **"Are you stuck"** and **"Is this even possible at this point?"** after repeated diagnostic APKs. A feasible result is **not yet delivered in Charoite Portal**, and further socket/RpcSs probes alone are not justified.

**Critical new public reference (reviewed October 28):** https://github.com/ashmerra/wehavephones — an independent Winlator-derived Battle.net and WoW Android project. README says users install and **sign in through actual Battle.net**, and documents a **Samsung Galaxy S26 Ultra** in tested devices. `docs/TESTED_DEVICES.md` specifies Galaxy S26 Ultra, SM-S948U, Android 16/One UI 8.5, logged in and reached WoW Classic Era **in-world gameplay** after manual completion by its account owner (Oct 16). See https://github.com/ashmerra/wehavephones/blob/main/docs/TESTED_DEVICES.md and https://github.com/ashmerra/wehavephones/issues/18 . This establishes a concrete example that hardware alone does NOT prohibit Battle.net login on the target phone. It does not establish that the user personally runs that app, that Charoite's current Wine supports it, that this result generalizes to all versions/devices, or that Diablo IV works.

**Documented working runtime** in https://github.com/ashmerra/wehavephones/blob/main/docs/WEHAVEPHONES_RUNTIME.md :
- `proton-10.0-34-arm64ec` (GE-Proton 10.0-34), patched Wine `ntdll.dll`/`ntdll.so` and `wineserver`; project also uses FEX execution infrastructure.
- `--disable-gpu --enable-features=NetworkServiceInProcess2` Chromium flags, `FEX_MULTIBLOCK=0`, `MESA_SHADER_CACHE_DISABLE=false`, `WINE_FDSAN_LEVEL=off`; per-device graphics configuration (including Turnip options).
- Project reports Proton 10 rendered Battle.net CEF, whereas their tested GE-Proton 11 variants did NOT (CEF browser/renderer Mojo connection timeout), demonstrating that blindly upgrading Wine/Proton can regress login. This is a **project-specific reported result**, not universal proof about all Proton 11.
- Their Build Assets docs describe pinned downloaded runtime assets and distinct runtime setup; this is a larger architectural change than extra command-line switches, not safe to transplant unreviewed into Charoite. Respect original attribution/licensing and pinned asset hashes.
- Charoite currently uses pinned upstream Winlator-derived Wine/Box64 runtime with per-environment Wine containers (see repo README and `.github/workflows/runtime-preview.yml`). **Proposed (NOT IMPLEMENTED):** an OPTIONAL separate Battle.net-compatible engine selection for Battle.net Gaming, using an isolated new prefix and never overwriting Touhou/TPDP existing runtime or user installation. Review architecture and possible dual-runtime asset footprint/licensing, then implement incremental authenticated pinned downloads/builds and compare same phone results before migrating/retiring any engine.
- Latest verified Charoite APK is GitHub Actions `40641148611` (code SHA `553d9cbd8dc49edc84016fda2adc83cb27c031b5`, 138 tests passed, artifact `12795777267`). **No APK was built in this feasibility-review turn.** A new runtime is NOT installed.
- **Diablo IV** needs separate compatibility/performance tests (64-bit Windows game, DirectX 12, substantial resources), and WoW success cannot be extrapolated to Diablo IV.

**Message to user:** This is technically possible, backed by an independently documented result even on Galaxy S26 Ultra, but not guaranteed to work with current Charoite engine. Acknowledge excessive prior incremental diagnostics without a working UI. Recommend runtime-level comparison with the functioning implementation, not further repetitive port/RPC testing. No uninstall or clearing existing data.

## 24. October 28, 2026 — Live architecture audit for separate Battle.net runtime (documentation only)

**Fresh GitHub verification:** At audit time Charoite `main` HEAD was `5a0bad3bcd68cf3803be14f0dfaace9b0caa1e88`, a documentation-only `[skip ci]` commit. Most recent successful Android workflow is [run 40641148611](https://github.com/rgarn023/CharoitePortal/actions/runs/40641148611), runtime source SHA `553d9cbd8dc49edc84016fda2adc83cb27c031b5`, artifact `Charoite-Portal-Android-APK` ID `12795777267` (unexpired on audit), 138 contract tests. No newer runtime build identified; this audit does not implement a new engine or APK.

**Source-grounded integration boundary:**
- `CharoiteEnvironments.java`: each realm maps to its own existing Winlator `ContainerManager` container ID, C: drive, registry/theme; attaching containers must never overwrite or re-create user data. There is **no independent per-environment Wine/FEX engine registry**.
- `CharoiteGameSessions.java`: launches the common `XServerDisplayActivity` with per-launch Intent flags and carefully Battle.net-scoped diagnostics. Engine selection is not currently modeled.
- `CharoiteCore.java` explicitly describes existing runtime as Winlator-derived Wine/Box64. `runtime-preview/overlay.py` modifies pinned upstream at build time. Replacing the Wine binary in an existing container is **not** equivalent to an isolated backend.
- Independent [WeHavePhones runtime documentation](https://github.com/ashmerra/wehavephones/blob/main/docs/WEHAVEPHONES_RUNTIME.md) describes **GE-Proton 10.0-34 ARM64EC**, FEX, patched ntdll+wineserver, additional ARM64 DLLs, device driver rules and Chromium's `NetworkServiceInProcess2`; its [app architecture](https://github.com/ashmerra/wehavephones/blob/main/docs/WEHAVEPHONES_APP.md) applies a verified single-runtime profile. Its [tested devices](https://github.com/ashmerra/wehavephones/blob/main/docs/TESTED_DEVICES.md) record reported S26 Ultra successful sign-in/in-world Classic Era but do not verify Charoite or Diablo IV.

**Next engineering stage (NOT IMPLEMENTED):** Study exact runner/asset build licenses, packaging size, hashes, Java launch hooks, FEX bridge and XServer lifecycle. Introduce a backend interface/descriptor that defaults to the existing Charoite engine for **all existing realms and containers**, with strict opt-in/rollback and explicit availability checks. Provision any candidate Proton+FEX runtime to a **new** app-private staging directory and **new** Battle.net test Wine container, using pinned manifests, integrity checks and atomic rename; don't mutate the existing Battle.net, TPDP, Touhou or other prefixes. Only after isolated native/runtime smoke tests and Android CI should an engine switch be exposed. Actual Galaxy sign-in and game tests remain required; never claim support based on build alone.

**Unchanged:** `com.charoite`, existing APK signing identity, every user's game/Wine/Blizzard data, and all currently installed runtimes. No code files or APK were changed during this audit.

## 25. October 28, 2026 — Charoite Core Next side-by-side implementation (modern engine NOT BUILT)

**User direction:** Preserve the current stable APK unchanged, create a separately installed next-gen edition integrating a **Charoite-maintained derivative of Wine/Proton Wine** with FEX/Box64 and graphics translation for Samsung Galaxy S26 Ultra. Aim for broad Steam/Battle.net Windows compatibility while respecting anti-cheat support; no kernel anti-cheat evasion/bypass or promise of universal compatibility. Original Charoite integration does **not** mean reimplementing all of Wine from scratch.

**Stable preserved:** existing `com.charoite` APK from [Actions 40641148611](https://github.com/rgarn023/CharoitePortal/actions/runs/40641148611), source `553d9cbd8dc49edc84016fda2adc83cb27c031b5`, artifact `12795777267`, 138 tests. Stable workflow `.github/workflows/runtime-preview.yml` was not edited and retains existing signing identity/data paths.

**Direct code committed to `main`:**
- `next-generation/rewrite_prefix_next.py`: reuse pinned upstream asset rewrite logic but swap fixed-width `com.winlator` to **`com.charoitx`**, never `com.charoite`. Distinct Android UID and filesystem roots.
- `next-generation/prepare_next.py`: after stable overlay, sets new `com.charoitx` application ID, **Charoite Next** label, distinct debug signing key path (`~/.android/charoite-next.keystore`), provider authority, native/Java path translation, embedded new engine status UI and reference manifest.
- `next-generation/CharoiteNextRuntime.java`: fail-closed runner inventory, bundled legacy Wine/Box64 initially usable; Proton ARM64EC/FEX and future Wine Staging/Box64 explicitly **not installed and launch blocked**.
- `next-generation/engine-reference.json`: pinned candidate Proton ARM64EC reference hash/source, provenance, required validation stages, anti-cheat limits; reference data ONLY, not a downloaded or distributed modern engine.
- `next-generation/tests/test_next_isolation_contract.py`: assertions for separate signing, Android package, no prefix migration, engine not-ready status, anti-cheat safety.
- `.github/workflows/charoite-next.yml`: independent Android APK CI builds pinned Winlator source with legacy functional Core overlay plus Next identity and runtime inventory, separate APK `Charoite-Next-Android.apk`, artifact name `Charoite-Core-Next-Android-APK`; does not overwrite stable artifact. Separate MIT-source attribution in legal bundle.
- `next-generation/charoite-wine/patches/` introduces first **attributed** upstream ARM64EC syscall/thread patch and Android file-owner patch from WeHavePhones. `next-generation/charoite-wine/README.md` includes source lineage, Wine LGPL and WeHavePhones MIT attribution/limitations; `UPSTREAM-WEHAVEPHONES-LICENSE.txt` preserves the full MIT license. `prepare-source.sh` pins the Proton-Wine source and **refuses to apply patches until GE/ARM64EC prerequisites explicitly verified**; nothing modifies installed Wine.

**Current boundary:** This is an actual side-by-side development edition foundation and source-controlled Wine patch baseline, **NOT yet a successfully built or usable Proton/FEX/Charoite Wine engine**. Do not claim Steam login/Battle.net spinner fixed, anti-cheat compatibility, DX12, or new Wine binaries shipped.

**First verified Next APK SUCCESS:** [Actions run 40649258138](https://github.com/rgarn023/CharoitePortal/actions/runs/40649258138), code SHA `aa89290a7e7a326ce495b6f3226f74adf8daf58a`, `Charoite-Core-Next-Android-APK` artifact ID `12799426447` (228,537,094 byte ZIP, uploaded and unexpired). 138 legacy regression tests + 6 Next isolation tests passed. Full Android build SUCCESS, Charoite Next app identity `com.charoitx` and separate signing verified, 8 native archives/173 paths rebased. Legal artifact ID `12799536112`. Later [skip ci] documentation-only commits may advance `main` beyond code SHA without a rebuild. **Galaxy S26 Ultra installation/device behavior NOT YET VERIFIED.** Modern modified Proton/FEX/Charoite Wine remains NOT compiled or bundled; no game compatibility claims.

**NEXT:** First achieve successful Next APK CI and phone install side-by-side; then implement an isolated reproducible Charoite Wine ARM64EC/FEX runner with source-built/pinned Wine `ntdll`/wineserver and FEX bridge in a NEW Next container. Smoke test portable Win32 program, Battle.net sign-in and Steam in separate newly created prefixes, record device evidence, retain a clean rollback. Only expose modern runner selection after all checks. No migration of existing `com.charoite` game data.

## 26. October 28, 2026 — First Charoite Wine source validation and host compilation

**User asked to begin building an original Charoite compatibility platform with Charoite-maintained modified Wine/Proton Wine, keeping the current stable app and the side-by-side Next APK safe.** This implementation step is **real Wine source preparation plus host build**, not yet an Android-compatible new runner.

**Code directly committed to existing GitHub `main`:**
- `next-generation/charoite-wine/prepare-source.sh` no longer accepts an unverified prerequisites environment flag. It clones pinned `The412Banner/proton-wine` SHA `c74acb09d51b447f5d5ac56c87608d3ec565a767` into a **new, nonexisting absolute workspace**, parses and applies exact source-defined Android/Bionic/FEX prerequisite patches, applies pinned GE fixes, then only vetted `patches/SERIES`. It refuses unknown patch entries, conflicts, fuzzy Charoite application and changed base SHA. Never installs Wine or touches Android prefix data.
- Initial imported upstream `0001` patch duplicated prior ARM64 suspension/SVE hunks. The source CI detected this. `patches/0100-arm64ec-syscall-stubs-and-thread-grace.patch` rebases the **additional** syscall dispatcher and thread grace changes onto the existing prerequisites. `patches/SERIES` selects 0100 plus attributed `0002-android-external-file-ownership.patch`; retains vendor 0001 as source provenance only. No claim all changes are Charoite-original; licensing and attribution retained.
- `next-generation/charoite-wine/tests/test_source_preparation.py` protects source SHA, new-workspace rule, selected patch series and no destructive/anti-cheat bypass commands.
- Added dedicated workflow `.github/workflows/charoite-wine-source.yml`; separated source builds from stable `.github/workflows/runtime-preview.yml` and the Next APK workflow (Next excludes Wine-source-only path). CI publishes source provenance + host compile report, not fake runnable Android Wine.
- Added `next-generation/charoite-wine/smoke-build-host.sh`. CI diagnosed/got past missing autogen-generated `configure` and missing pinned `dlls/winedirectaudio.drv` submodule; the script now initializes the pinned submodule, regenerates Wine's source with `autogen.sh`, runs minimal Linux configure, and actually compiles `server/wineserver` without installing it.

**VERIFIED success:** [GitHub Actions run 40709722718](https://github.com/rgarn023/CharoitePortal/actions/runs/40709722718), source code SHA `c4292c9e78cb5c81607b6166d26031078e807a38`, both jobs **SUCCESS**. Patch trace reports **70** pinned Android/Bionic/FEX prerequisites, **10** GE fixes, **2** Charoite-managed active patches. Native host compilation includes `server/token.o`; resulting `server/wineserver` is **ELF64 Linux x86-64**, `--version` outputs **Wine 10.0**. Artifacts: `Charoite-Wine-Source-Validation` ID **12824344954** and `Charoite-Wine-Host-Build-Validation` ID **12825407581** (both report-only). Subsequent documentation-only `[skip ci]` commits advance main without modifying that verified code or producing a new APK.

**STRICT limitations:** No Android ARM64EC `ntdll.dll`, Unix `ntdll.so`, Android `wineserver`, FEX bridge, DXVK/VKD3D integration or new prefix is yet built/tested. No new Charoite Wine runner installed in Charoite Next. No Battle.net/Steam login or game/anti-cheat functionality verified. A Linux host build does not prove Android execution, and the Android-specific `__ANDROID__` path was not exercised by this host compilation.

**Preserved reference builds:** stable Portal `com.charoite` [Actions run 40641148611](https://github.com/rgarn023/CharoitePortal/actions/runs/40641148611); independently installable Next `com.charoitx` [Actions run 40649258138](https://github.com/rgarn023/CharoitePortal/actions/runs/40649258138). Never uninstall/clear old app or migrate Wine prefixes.

**Exact next step:** implement a pinned Android 16-KiB-compatible NDK + LLVM-MinGW ARM64EC build using the now-valid source and native ABI checks; build patched ARM64EC `ntdll.dll`/`ntdll.so` and Android `wineserver`, then stage in a new app-private Next runner directory, validate hashes, create separate new Windows prefix; only then test Windows program, Battle.net and Steam on Galaxy S26 Ultra. Keep developer attribution and anti-cheat non-bypass boundary.

## 27. October 28, 2026 — Android ARM64 Charoite Wine server and machine-ID safety fix

**User instruction:** Continue developing Charoite Core Next / Charoite Wine directly on GitHub, preserve original `com.charoite` and independent Next `com.charoitx`, no reinstall/deletion or replacing game data. User interrupted with “Are you stuck?” and was told the native build succeeded.

**Implementation committed to `main`:**
- `next-generation/charoite-wine/build-android-arm64.sh`: explicit prepared-source check, pinned Android NDK r27d, API 35 AArch64 clang, native host tools, isolated Android Wine configure, build `server/wineserver` including patched `server/token.c`, verify ARM64 ELF type and all `PT_LOAD` p_align at least 16,384 bytes. Output only in dedicated CI artifacts, never installed in either Android app or game prefix.
- New `android-arm64-wineserver` job in `.github/workflows/charoite-wine-source.yml`; runs after source validation and alongside existing x86-64 host smoke test. Emits experimental `Charoite-Wine-Android-ARM64-Experimental` artifact without claiming it is runnable standalone.
- Native source-build warning revealed Wine upstream's Android `init_user_sid` path could leave `FILE *f` uninitialized. Charoite-authored `patches/0200-android-machine-id-fallback.patch` initializes pointer and falls back to deterministic UID-derived 16-digit machine ID when no per-prefix file is available. Added to `patches/SERIES`; preparation enforces 3 active patches; tests and attribution updated.
- `next-generation/charoite-wine/tests/test_android_build_contract.py` guards Android NDK/ABI/16-KiB checks and non-destructive isolation. Existing Wine tests updated.

**Verified full success:** [Actions run 40715586360](https://github.com/rgarn023/CharoitePortal/actions/runs/40715586360), source commit `244cf07400b7f5603d4f153bee5b034eadfcb73b`, all **3 jobs succeeded**: patch preparation, Linux host `wineserver` build, experimental Android AArch64 `wineserver`. Android ELF alignment verified `[16384,16384,16384,16384]`. The former uninitialized-file-pointer warning disappeared. A remaining upstream unused `anonymous_logon_sid` warning is not fatal.

Artifacts at this run:
- `Charoite-Wine-Android-ARM64-Experimental`, artifact **12828870997** (Android-native server, hash and ELF inspection reports; **not an APK**).
- `Charoite-Wine-Host-Build-Validation`, artifact **12828840652** (host build report).
- `Charoite-Wine-Source-Validation`, artifact **12828611014** (source provenance and patch report).

**Important:** This **is not yet ARM64EC Wine/Proton running on Android**. `wineserver` is just one Android-native process. ARM64EC Windows `ntdll.dll`, Unix `ntdll.so`, loader, FEX, graphics, prefix provisioning and device-based Steam/Battle.net sign-in remain unbuilt/untested. Respect original `com.charoite` data; do not replace the existing Charoite Next APK until actual modern runtime integration passes. No unsupported anti-cheat bypass.

**Next implementation step:** pin the LLVM-MinGW ARM64EC toolchain with SHA256 and build the ARM64EC PE `ntdll.dll`, paired Android `ntdll.so`, and ABI/checksum verification as separate, non-installing CI artifacts. Then integrate a verified runnable runner in a **new** Next-only prefix.

## 28. October 28, 2026 — ARM64EC Wine ntdll cross-compilation

**User request:** “Please continue. Are you documenting handoffs in github”. **Answer: YES**, continuously at this `docs/CURRENT_HANDOFF.md` on the existing `main` branch. Last verified full native build prior to this phase remains [Actions 40715586360](https://github.com/rgarn023/CharoitePortal/actions/runs/40715586360), which produced a *standalone experimental Android ARM64* `wineserver` with 16 KiB `PT_LOAD` alignment and machine-ID safety patch 0200. No Android runner was installed.

**New work committed on `main`:**
- `next-generation/charoite-wine/build-arm64ec-ntdll.sh`: **new isolated ARM64EC ntdll build** using pinned source (`c74acb09d51b447f5d5ac56c87608d3ec565a767`), GE+Bionic/FEX/Charoite patch queue, NDK r27d (API 35), and SHA-256 pinned LLVM-MinGW 20261020 UCRT toolchain. Builds Windows ARM64EC PE `ntdll.dll` plus Android AArch64 Unix `ntdll.so`, checks the PE machine is ARM64EC (0xA641 rather than ordinary ARM64) and Unix ELF PT_LOAD 16 KiB alignment, emits hashes. **Experimental; no installation**.
- New `android-arm64ec-ntdll` job in `.github/workflows/charoite-wine-source.yml` downloads `llvm-mingw-20261020-ucrt-ubuntu-22.04-x86_64.tar.xz`, expected SHA-256 `55064b60b991a1e1e8090b8c2f84e82b22cfe5903d12c159d65064cf5e8ae335`. Only publishes `Charoite-Wine-ARM64EC-NTDLL-Experimental` after strict successful build.
- `next-generation/charoite-wine/tests/test_arm64ec_contract.py` safeguards PE arch distinct from AArch64, pinned toolchain, source check, no user app mutation and separate artifact.
- Prior standalone Charoite Next `com.charoitx` and stable Portal `com.charoite` APK workflows are deliberately untouched. No changes to any existing game prefix/data.

**ARM64EC CI iteration (in-progress):** Initial [Actions run 40719387480](https://github.com/rgarn023/CharoitePortal/actions/runs/40719387480) source validation passed; the pinned LLVM-MinGW cross-compiler produced a verified **ARM64EC PE object (0xA641)**, but hybrid code compilation failed on an x86-only `__fastfail` asm constraint in Wine `include/winnt.h`. Charoite-authored `patches/0300-arm64ec-fastfail-instruction.patch` now chooses native ARM64 `brk` for `__arm64ec__`. A malformed patch header was corrected. [Run 40720332734](https://github.com/rgarn023/CharoitePortal/actions/runs/40720332734) validated the four active Charoite patches and compiled Linux host Wine successfully, but the ARM64EC job stopped at a nonexistent `arm64ec-windows/ntdll.dll` Makefile target. Wine 10 actually builds the hybrid target as `aarch64-windows/ntdll.dll` with ARM64EC-specific dependencies; **the final PE machine type still must be checked, not inferred from path**. Corrected source and tests in commits `2f8d9232` / `a713337a`. The next CI run [40720915045](https://github.com/rgarn023/CharoitePortal/actions/runs/40720915045) is testing that corrected target. **Do not claim ntdll PE/SO built until it passes.** Older Android ARM64 server build 40715586360 remains green.

**Engineering next steps:** Fix actual ARM64EC cross-compiler/build failures shown by CI (if any); require real PE machine 0xA641 and Android ELF ABI before describing the ntdll pair as compiled. Next create isolated Charoite Next runner slot, test FEX bridge, graphics and prefix on Galaxy S26 Ultra. Never bypass anti-cheat or claim Battle.net/Steam games work without device tests.

## 29. October 28, 2026 — VERIFIED ARM64EC ntdll and Android Unix ntdll pair

**User request:** “Please continue. Are you documenting handoffs in github?” Yes, the definitive handoff remains `docs/CURRENT_HANDOFF.md` on existing branch `main`. ChatGPT directly implemented new source, patches, workflows and tests on GitHub without touching either installed Android edition or the stable app CI.

**The previous section 28's pending ARM64EC result has now been superseded by successful compilation.** This phase had real compiler problems, diagnosed and corrected in source-controlled Wine patches; failed runs are intentionally retained for traceability:
- [40719387480](https://github.com/rgarn023/CharoitePortal/actions/runs/40719387480): first ARM64EC probe correctly emitted PE machine 0xA641, but Wine `include/winnt.h` used x86-only fastfail instruction with invalid register constraint on ARM64EC.
- [40720190029](https://github.com/rgarn023/CharoitePortal/actions/runs/40720190029): source patch 0300 hunk-count malformed; corrected and passed subsequently.
- [40720332734](https://github.com/rgarn023/CharoitePortal/actions/runs/40720332734): source validation passed; cross-build requested nonexistent `arm64ec-windows/ntdll.dll` target, corrected to Wine 10's real `aarch64-windows/ntdll.dll` target (which includes ARM64EC hybrid objects). Final PE machine type is verified rather than assumed from path.
- [40720915045](https://github.com/rgarn023/CharoitePortal/actions/runs/40720915045): compilation reached ARM64EC hybrid `heap.c` and `loader.c`, but x86 `lock; xchg` atomic assembly emitted invalid AArch64 instructions. Added Charoite-authored `0400-arm64ec-atomic-operations.patch`: compiler atomic builtins for exchange/pointer exchange and explicit ARM64EC acquire/release atomics.

**Success:** [**GitHub Actions run 40721844963**](https://github.com/rgarn023/CharoitePortal/actions/runs/40721844963), compiled code SHA **`26c7a33c7cd6207123211c1c1af20df47c62e167`**. **ALL FOUR JOBS PASSED**: `validate-wine-source`, `smoke-build-host-wineserver`, `android-arm64-wineserver`, `android-arm64ec-ntdll`. Charoite Wine source queue contains 5 active patches: `0100`, `0002`, `0200`, `0300`, `0400`; additionally 70 Android/Bionic/FEX base prerequisite and 10 GE patches. Original vendor `0001` remains retained only as attribution reference to avoid double-applying duplicate hunks.

**Verified binary artifacts for this run:**
- `Charoite-Wine-ARM64EC-NTDLL-Experimental` — artifact ID **12831021769**, ~949,460 bytes ZIP. Includes `ntdll-arm64ec.dll` Windows PE machine **IMAGE_FILE_MACHINE_ARM64EC (0xA641)** and `ntdll-arm64-android.so` Android ELF AArch64; its four `PT_LOAD` p_align values are **[16384,16384,16384,16384]**. Includes build report, hashes and headers.
- `Charoite-Wine-Android-ARM64-Experimental` — artifact ID **12829954961**, AArch64 Android wineserver plus build/ELF reports.
- `Charoite-Wine-Host-Build-Validation` — artifact ID **12831640935**.
- `Charoite-Wine-Source-Validation` — artifact ID **12830373158**.

**Implemented directly in repository:**
- `next-generation/charoite-wine/build-arm64ec-ntdll.sh` (NDK/API35 and pinned LLVM-MinGW SHA256, host-tool configure, hybrid ARM64EC PE cross compiler probe, simultaneous ntdll PE and Unix .so compilation, fail-close PE machine check, 16 KiB ELF ABI and hash report, no installation).
- `.github/workflows/charoite-wine-source.yml` independent ARM64EC ntdll CI job; does **not** modify Next or stable APK workflows.
- `next-generation/charoite-wine/patches/0300-arm64ec-fastfail-instruction.patch`, `0400-arm64ec-atomic-operations.patch` (Charoite-authored Wine derivative modifications).
- `next-generation/charoite-wine/tests/test_arm64ec_contract.py` plus updated source patch count tests. All CI validations passed.
- `next-generation/charoite-wine/README.md` updated with the complete verified run and artifacts.

**Limitations:** These are independently compiled components, **not yet a functioning full Android Wine/Proton/FEX runtime, not an APK and not yet device-tested**. The modern launcher engine is still marked **NOT READY**. CI does not establish Battle.net, Steam, Diablo IV, a graphics pipeline or any particular anti-cheat compatibility. No kernel anti-cheat bypass or integrity-check manipulation will be implemented.

**Preserved editions:** stable Charoite Portal `com.charoite` [run 40641148611](https://github.com/rgarn023/CharoitePortal/actions/runs/40641148611); side-by-side Charoite Next `com.charoitx` [run 40649258138](https://github.com/rgarn023/CharoitePortal/actions/runs/40649258138). Do not uninstall, clear storage, replace prefixes or mutate user installed games.

**Exact next engineering milestone:** assemble and ABI-check a complete Android-native ARM64EC Wine 10 package from our source plus a pinned FEX bridge and DirectX-to-Vulkan drivers. Implement atomic/hashes-first staging and rollback into **new** Next-only runner slot, create a new isolated Wine prefix, then on-device baseline tests and Battle.net/Steam scenarios. Maintain separate source/build artifacts and device diagnostics.

## 30. October 28, 2026 — Same-source ARM64EC Wine loader/server/ntdll runtime slice

**Goal:** Advance beyond separately compiled Charoite Wine components by compiling the ARM64EC PE `ntdll.dll`, Android AArch64 Unix `ntdll.so`, Android `wineserver`, and Android `wine` loader **in one Wine configure/build tree**, then publish a reproducible, read-only, ABI and SHA-256 verified **experimental** package. No current Charoite app APK, game data, legacy Wine prefix, installer or runtime switch changed. Preserve stable `com.charoite` and standalone Next `com.charoitx`.

**Changes committed directly on existing `main`:**
- `next-generation/charoite-wine/build-arm64ec-ntdll.sh`: after compiling the two ntdll components, also compiles `make server/wineserver loader/wine` from the **same** Android ARM64EC build tree, and invokes a separate safe bundle packager with absolute script path.
- `next-generation/charoite-wine/package-runtime-slice.py`: verifies all 4 binary architectures, PE machine **0xA641**, AArch64 ELF `PT_LOAD` minimum 16 KiB alignment, runtime library dependencies, independent SHA-256 and size; produces `charoite-wine-arm64ec-base-slice.tar.gz` and deterministic, fail-closed `manifest.json` with `launch_ready=false` and `installable=false`. Archive uses no symlinks or unsafe extraction paths.
- `next-generation/charoite-wine/verify-runtime-slice.py`: read-only verification of archive manifest, exact member list, path safety, binary SHA-256 and architecture metadata. Never unpacks or installs files.
- `next-generation/charoite-wine/tests/test_runtime_slice.py`: synthetic tests verify good archive, tampering rejection, bad PE machine, 4 KiB rather than 16 KiB rejection, and overwrite refusal. CI source-validation stage runs tests.
- `.github/workflows/charoite-wine-source.yml`: existing independent native tests retained; experimental `android-arm64ec-ntdll` job now additionally verifies and uploads separate `Charoite-Wine-ARM64EC-Base-Slice-Experimental` artifact only after all bundle checks.
- **Never** enable modern Proton/FEX engine in Charoite Next merely from the package's existence. FEX, full Wine DLL tree, DirectX/Vulkan, display/input, genuine prefix provisioning, Battle.net/Steam and device compatibility **NOT YET IMPLEMENTED**.

**CI diagnostic and fix:** [Run 40726234534](https://github.com/rgarn023/CharoitePortal/actions/runs/40726234534) passed source tests, Linux host build, standard Android ARM64 wineserver; the new hybrid build **successfully compiled all FOUR** PE/ELF components but failed during packaging because a relative shell script path was resolved after switching working directory to the Wine build tree. Fixed by computing `script_dir` as an absolute path before `cd`, commit `2a7454af195ddeb70c7b707a07cfa91a379bbbab`.

**VERIFIED initial package success:** [Run 40727103047](https://github.com/rgarn023/CharoitePortal/actions/runs/40727103047), compiled commit `2a7454af195ddeb70c7b707a07cfa91a379bbbab`, all four CI jobs **SUCCESS**. The Android ARM64 `wine` loader, `wineserver`, Unix `ntdll.so`, and ARM64EC PE `ntdll.dll` compiled from one source/configuration. Binary archive packager passed `CHAROITE_WINE_SLICE_ABI_CHECK=PASS` and separate `CHAROITE_WINE_SLICE_ARCHIVE_VERIFIED=PASS`; archive was explicitly `LAUNCH_READY=false`. Artifact `Charoite-Wine-ARM64EC-Base-Slice-Experimental` **12832908434**.

**VERIFIED latest source-attributed package:** [GitHub Actions run 40728026115](https://github.com/rgarn023/CharoitePortal/actions/runs/40728026115), code SHA `fae65c2491e1778cabd323dec507662feed82092`, **all four jobs SUCCESS**, **21 source/archive tests passed**. New artifact `Charoite-Wine-ARM64EC-Base-Slice-Experimental` ID **12834111695**, ZIP size **1,275,326 bytes** (contains inner `charoite-wine-arm64ec-base-slice.tar.gz`, validation report and manifest). This replaces the original package as the latest verified checkpoint. Package content includes 4 coherent native components plus `COPYING.LIB`, `LICENSE`, attributed vendor MIT notice and exact `charoite-source-delta.patch` from Wine upstream SHA `c74acb09d51b447f5d5ac56c87608d3ec565a767`. Both binary and source/license files are individually SHA-256 verified in a fail-closed manifest; archive path safety and 16 KiB/ARM64EC ABI checks passed. Explicit flags `launch_ready=false`, `installable=false` remain enforced.

**Additional artifacts (same latest run):** standalone `Charoite-Wine-ARM64EC-NTDLL-Experimental` **12833398102**; `Charoite-Wine-Android-ARM64-Experimental` **12833862177**; source provenance `Charoite-Wine-Source-Validation` **12833219346**; Linux host report `Charoite-Wine-Host-Build-Validation` **12834051928**.

**Changes after first package:** `package-runtime-slice.py` now includes and hashes Wine LGPL/license/attribution/corresponding source patch delta; `verify-runtime-slice.py` checks their exact paths and hashes; `tests/test_runtime_slice.py` exercises source file tampering. These are source-provenance improvements, not new Wine execution claims.

**Next after success:** audit actual ELF dynamic `NEEDED` dependencies and Android executable path assumptions, then source/package other Wine runtime DLLs, NLS, FEX and graphics into a versioned, checksum-verified Next-only runtime slot. Only after completeness and phone smoke tests should the modern runner selector become runnable.

## 31. October 28, 2026 — ARM64EC kernel32 and kernelbase bootstrap DLLs

**User:** “Let's continue”. Continue Charoite Core Next independently on GitHub `main`, preserve existing stable `com.charoite` and side-by-side `com.charoitx`, all user prefixes/games and stable/Next APKs. The most recent validated component baseline remains [Wine CI 40728026115](https://github.com/rgarn023/CharoitePortal/actions/runs/40728026115), source-attributed four-component archive artifact **12834111695**, 21 tests, four jobs green.

**Next source change implemented:** compile additional *Windows ARM64EC* bootstrap DLLs from the **same** already-built and source-validated ARM64EC Wine configuration: `dlls/kernelbase/aarch64-windows/kernelbase.dll` and `dlls/kernel32/aarch64-windows/kernel32.dll`. The Wine 10 Makefile graph uses the `aarch64-windows` output location for hybrid ARM64EC DLLs; **actual PE machine (0xA641) must be validated**, not assumed from directory. No user-visible engine readiness change.

**Commits/new files:**
- `next-generation/charoite-wine/build-kernel-bridge.sh`: refuses unchecked Wine source and existing output, requires prior ntdll in same tree, compiles both kernel DLLs, verifies each PE `IMAGE_FILE_MACHINE_ARM64EC (0xA641)` via pinned `llvm-readobj`, saves SHA-256 and machine metadata; output isolated and explicitly `installable=false`, `launch_ready=false`.
- `next-generation/charoite-wine/verify-kernel-bridge.py`: read-only verification of hashes, PE machine report, exact expected files and disabled state.
- `next-generation/charoite-wine/tests/test_kernel_bridge.py`: tests source isolation and no destructive paths, both DLLs, altered bytes rejection, normal ARM64 PE rejection, unsafe ready flag rejection and extra files rejection.
- `.github/workflows/charoite-wine-source.yml`: after the previously verified base-slice artifact is published, executes kernel bridge compilation and metadata verification. On success publishes a separate `Charoite-Wine-ARM64EC-Kernel-Experimental` artifact.
- The original `Charoite-Wine-ARM64EC-Base-Slice-Experimental` job steps remain unchanged and publish before this new stage; a failed kernel stage never contaminates prior known-good bundles.

**CI diagnostic and active fix:** [Run 40738747087](https://github.com/rgarn023/CharoitePortal/actions/runs/40738747087) passed source validation, host Wine build, independent Android ARM64 wineserver, and published the known-good native base slice, but **kernelbase/kernel32 failed at final PE link** with `clang: no such file or directory: 'libgcc.a'`. The patched Wine host `tools/winegcc/winegcc.c` unconditionally added the Clang cross-compiler's `-print-libgcc-file-name` result to ARM64EC `-nodefaultlibs` linking, even when bare `libgcc.a` does not exist in the pinned Clang-only toolchain. Charoite-authored new `patches/0500-arm64ec-no-spurious-libgcc.patch` suppresses this libgcc fallback **only** for `CPU_ARM64EC` + explicit `nodefaultlibs` + `no_default_config`; all other targets remain unchanged. Series now contains 6 active Charoite patches (+70 upstream prereqs, +10 GE). Preparation and tests enforce counts.

**Validated final outcome:** [GitHub Actions run 40739844466](https://github.com/rgarn023/CharoitePortal/actions/runs/40739844466), source SHA **`fc561a467c60a756ebd136f92091c0bb44a1a210`**, **all four jobs SUCCESS**: source patch validation, host Wine build, Android AArch64 wineserver, Android ARM64EC ntdll/loader/kernel module build. The earlier run [40739727774](https://github.com/rgarn023/CharoitePortal/actions/runs/40739727774) stopped at a source-provenance test because README did not yet mention patch 0500; adding its explicit attribution and scope fixed that test.

**New verified artifact:** `Charoite-Wine-ARM64EC-Kernel-Experimental` **12838573488** (~961,805 bytes ZIP), contains **`kernelbase-arm64ec.dll` and `kernel32-arm64ec.dll`**, each verified with `llvm-readobj` PE machine **IMAGE_FILE_MACHINE_ARM64EC (0xA641)**, individually SHA-256 recorded and independently verified against `kernel-bridge-manifest.json`. Both DLLs link successfully with the targeted Clang/Wine `libgcc.a` correction. Kernel artifact metadata sets `launch_ready=false`, `installable=false`, and requires the independently built base slice.

**Other same-run artifacts:** latest known-good `Charoite-Wine-ARM64EC-Base-Slice-Experimental` **12837799898**, `Charoite-Wine-ARM64EC-NTDLL-Experimental` **12838443793**, `Charoite-Wine-Android-ARM64-Experimental` **12838564522**, source validation **12839490543**, host build report **12839820086**. All GitHub artifacts are CI products, not APKs or installable game engines.

**Next milestone:** build Wine's `wineboot.exe` (and the transitive Windows API libraries it imports), verify ARM64EC PE type, then progressively assemble the entire compatible DLL/NLS and FEX/graphics stack. Create and test an isolated Next-only Wine prefix before enabling game launches. No end-to-end device, Battle.net, Steam or anti-cheat success has yet been demonstrated.

**Boundaries:** This work does not create an installable Android APK, working prefix, complete Wine/Proton, FEX or Vulkan graphics environment; does not solve Battle.net login/Steam/Diablo IV or publisher anti-cheat support. If kernel PE libraries compile, the next candidate is Wine boot services (`wineboot.exe` and dependencies), full DLL tree, Android/FEX bridge, prefix and phone tests, all in a new Next-only runner slot.

## 32. October 28, 2026 — Wineboot Windows startup PE cross-compilation

**User instruction:** continue development directly on connected `rgarn023/CharoitePortal` `main`, maintain GitHub handoffs; preserve original stable Portal and side-by-side Next private storage, game installations, prefixes and APKs.

**Verified previous milestone:** [Actions run 40739844466](https://github.com/rgarn023/CharoitePortal/actions/runs/40739844466), all four jobs SUCCESS; ARM64EC Windows `kernelbase.dll` and `kernel32.dll` verified machine 0xA641, `Charoite-Wine-ARM64EC-Kernel-Experimental` artifact **12838573488**, source patch 0500 fixed Clang/winegcc spurious `libgcc.a` link.

**New implementation:**
- `next-generation/charoite-wine/build-wineboot.sh` compiles `programs/wineboot/aarch64-windows/wineboot.exe` from the **same** patched Wine 10 Android ARM64EC tree after verifying `ntdll`, `kernelbase`, `kernel32`; lets Wine build the transitive API imports; checks the resulting PE machine type 0xA641 and creates a SHA-256 manifest that explicitly says `compiled-not-executed`, `prefix_created=false`, `launch_ready=false`, `installable=false`.
- `next-generation/charoite-wine/verify-wineboot.py` independently checks exact file inventory, hashes, PE header and hard-disabled engine/prefix state.
- `next-generation/charoite-wine/tests/test_wineboot.py` covers no destructive app/prefix paths, expected Wine Makefile target and dependencies, tampering, invalid launch-ready and false prefix-created flags.
- `.github/workflows/charoite-wine-source.yml` runs this stage **after** the known-good base slice and ARM64EC kernel DLL artifacts are independently published, then uploads a separate `Charoite-Wine-ARM64EC-Wineboot-Experimental` artifact only on successful PE ABI and manifest checks.
- No installed Android binaries or data have been touched. This does not prove Android can execute `wineboot` or create a prefix; full Wine DLL/Unix and FEX/graphics dependencies remain missing.

**CI diagnostic and correction:** [Run 40740753269](https://github.com/rgarn023/CharoitePortal/actions/runs/40740753269) passed source validation, Linux host compilation, Android `wineserver`, the four-component ARM64EC source-built base package and the ARM64EC kernelbase/kernel32 modules. **Failed only when linking `wineboot.exe`**: Wine uses `aarch64-w64-mingw32` for the regular Windows PE startup program, unlike the hybrid ARM64EC kernel DLLs. The `winegcc` wrapper again incorrectly added nonexistent `libgcc.a` in Clang `--no-default-config` mode. Updated Charoite-maintained `0500-arm64ec-no-spurious-libgcc.patch` to omit the GCC archive for **CPU_ARM64 OR CPU_ARM64EC** when `no_default_config`, retaining GCC handling on all other targets; README/attribution updated, patch SHA commit `0991e7631ba293a8311f2c26443d81f706c03e46`.

**Follow-up CI result:** [Run 40741678946](https://github.com/rgarn023/CharoitePortal/actions/runs/40741678946) passed source prep, Linux host Wine, Android ARM64 server, ntdll and both ARM64EC kernel libraries. Wine's `wineboot.exe` **compiled and linked successfully**, with the spurious `libgcc.a` issue now resolved for CPU_ARM64 / CPU_ARM64EC. The packaging script then rejected the executable because it required ARM64EC (0xA641), but the actual Wine Makefile uses `-b aarch64-w64-mingw32`; correct expected architecture is **regular Windows ARM64 (0xAA64)**. Keep the distinction explicit; do not relabel valid ARM64 output as hybrid ARM64EC.

**Corrective changes:** `build-wineboot.sh`, `verify-wineboot.py` and associated unit tests now require Wineboot PE machine `0xAA64` and output `wineboot-arm64.exe` (instead of `wineboot-arm64ec.exe`). Workflow artifact renamed to `Charoite-Wine-ARM64-Wineboot-Experimental`. Fixed an additional SHA manifest-generation path typo in `build-wineboot.sh` (final code commit `fdaff1dbb1dc80a9c40528503c86faf16314c392`).

**CI follow-up:** [Run 40742611230](https://github.com/rgarn023/CharoitePortal/actions/runs/40742611230) passed source preparation and compiled `wineboot.exe` without linker errors, but the **ABI grep check was incorrectly double-escaped**: `grep -E` received two backslashes before the parentheses and could not match `IMAGE_FILE_MACHINE_ARM64 (0xAA64)`. Confirmed via a synthetic local GNU grep test (double escape returns 1, single escaped parentheses return 0). Corrected `build-wineboot.sh` to use one escaped regex backslash; also prints `llvm-readobj --file-headers` report to CI log before matching. Added regression assertions in `tests/test_wineboot.py` to prevent double-escaped matching. Final source commit `34afe19065761f80f830fd651d33532326930f80`.

**Latest run to verify:** [Actions 40743283497](https://github.com/rgarn023/CharoitePortal/actions/runs/40743283497) queued for the corrected grep verifier and regression test. **Pending at handoff update**. Must confirm actual `Machine` emitted and published `Charoite-Wine-ARM64-Wineboot-Experimental` ID; do not infer successful package from successful PE linker command.

**Next milestone if successful:** include boot utility, kernel modules and source-verified base in a coherent compatible Wine package; progressively build required Unix/PE DLLs, FEX and graphics stack; device-test on Galaxy S26 Ultra in a **fresh isolated Next-only** Wine prefix before enabling the modern engine. Do not imply Battle.net/Steam/Diablo IV or unsupported anti-cheat works.

---
**End of current Charoite Portal handoff.**
