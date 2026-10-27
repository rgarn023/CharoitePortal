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
- **Runtime code SHA:** `aa29752deebe5708c6d823384107e701f450c0a2`.
- **GitHub Actions run `40586875588`** — **SUCCESS**: https://github.com/rgarn023/CharoitePortal/actions/runs/40586875588
- **APK artifact:** `Charoite-Portal-Android-APK`, artifact ID **12772202008**, ZIP archive **231,423,080 bytes**, verified not expired.
- Native Win32 helper, **126 regression tests passed** (verified in final GitHub Actions logs), Android APK and signing checks passed. **The latest temporary RpcSs startup repair has NOT yet been tested on the Galaxy.** Documentation-only commits can advance `main` beyond the APK's runtime SHA without changing code.
- Android package ID `com.charoite` stays unchanged. No Touhou/General environment code changes. The only service configuration change is gated behind explicit user confirmation inside **Battle.net Gaming**, with in-session rollback to original Disabled startup type and a recovery marker for interrupted attempts. It is experimental; restoration MUST be verified in on-device report, not merely assumed.

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

**Current priority (October 27):** The user's actual on-device report from run `40586875588` confirms the opt-in Battle.net RpcSs startup experiment worked: SERVICE_RUNNING for 16/16 samples, `monitor_rpc_start_win32_error=0`, original start type 4=Disabled, and **`monitor_rpc_restore_confirmed=1`** with no errors. The Blizzard client and Agent remain present; the UI outcome (login vs spinner) has **not been reported**. Ask **one direct question: did Battle.net reach the login screen or is it still spinning?** Do not infer the answer from process/service counts. If still spinning, investigate whether the helper starts too late (first X11 window vs launch), then CEF rendering and IPC; preserve the working scoped RpcSs activation and rollback. No new runtime code or APK built after the verified `40586875588` source SHA; handoff-only commit advances main.


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

---
**End of current Charoite Portal handoff.**
