## 2026-11-23 04:20 UTC — Meteorite Alpha build 1188 published; on-device v19 graphics pending

- **Galaxy prior v18:** Exit 15 = neither Windows client nor screen pixel purple despite 360×220 native surface registration; no Android frame-update event in checkpoint. Do not repeat consumed v18 or modify earlier tests. Foreground screen-awake already works.
- **Native code implemented:** [PR #56](https://github.com/rgarn023/CharoitePortal/pull/56) requests real visible-HWND GDI redraw after Android native-surface refresh. [Provider 45105262930](https://github.com/rgarn023/CharoitePortal/actions/runs/45105262930) and [postbuild 45105717342](https://github.com/rgarn023/CharoitePortal/actions/runs/45105717342) **SUCCESS**. All matching native source/ZIP/PE/ELF SHA256SUMS independently verified; host and display driver binaries byte-identical.
- **v19 APK RELEASED:** [PR #59](https://github.com/rgarn023/CharoitePortal/pull/59) merges exact artifact pins and fail-closed native cohort check; [Android Actions 45110695253](https://github.com/rgarn023/CharoitePortal/actions/runs/45110695253) **SUCCESS**; official signed [Meteorite Alpha 1188](https://github.com/rgarn023/CharoitePortal/releases/tag/charoite-next-vc1188) published with APK. New private one-shot v19 is ready; no actual Galaxy test yet. Duplicate PR #58 closed.
- **One action needed:** Owner updates in-app to 1188 and runs one isolated v19 window test. Record Win32 15/16/17/42 status, Android presentation frame checkpoint, and native log on failure. If still 15, work on native GDI dirty flush/queue after surface registration, not repeated desktop-only repaints.
- **Preservation/progress:** Stable Portal, games, saves, user prefixes/rootfs, all v1–v18 scratch untouched. Approximate v1.0 readiness remains 40%.

## 2026-11-23 — Verified v19 native driver candidate packaging

- **Native fix already merged:** [PR #56](https://github.com/rgarn023/CharoitePortal/pull/56) requests GDI redraw after visible CPU HWND receives Android native surface. [PR #57](https://github.com/rgarn023/CharoitePortal/pull/57) stages fresh isolated v19 one-shot. Duplicate PR #58 closed. v18 owner test exited 15 with no updated Android frame.
- **Provider + postbuild GREEN:** [45105262930](https://github.com/rgarn023/CharoitePortal/actions/runs/45105262930) and [45105717342](https://github.com/rgarn023/CharoitePortal/actions/runs/45105717342). Downloaded and verified artifact archives and internal SHA256SUMS: native host 14786954701, Explorer 14786854846, display 14787417115. Native host and separate display binaries **byte-identical**.
- **Next candidate:** `fix/wine29-v19-native-artifact-pins` repins exact output hashes into the experimental official APK workflow, verifies display cohort matches native host, preserves strict v18 GDI repaint Windows fixture and makes a *new* v19 scratch. Source-only CI, signed Android APK and device runtime pending; do not yet call v19 released.
- **Safety:** Do not access stable Portal or wipe games, saves, rootfs, user prefixes or prior tests. Estimated completion 40%.

## 2026-11-23 — v19 native provider build, source implemented

- **v18 Galaxy failure:** registered window and texture but exit 15 (neither Win32 client nor desktop screen purple); no Android updated frame. Do not reuse v18.
- **Code merged:** [PR #56](https://github.com/rgarn023/CharoitePortal/pull/56) adds visible-HWND native surface-refresh invalidation / GDI repaint; preserves GL and stringent pixel proof. [Provider run 45105262930](https://github.com/rgarn023/CharoitePortal/actions/runs/45105262930) running, patch checks passed and ARM64 module compilation underway; not yet a driver build success.
- **Isolation merged:** [PR #57](https://github.com/rgarn023/CharoitePortal/pull/57) reserves distinct v19 scratch and latest-log recovery, preserving v1–v18, static CI passed. No APK release yet.
- **Next:** verified source-matched ARM64 PE + ELF and Java host hashes → new signed experimental APK → one owner-approved Galaxy v19 runtime test. Overall ~40%. Do not touch stable Portal, games or prefix data.

## 2026-11-23 — Native GDI refresh fix and isolated v19 preparation

- **P0 new native fix:** [PR #56](https://github.com/rgarn023/CharoitePortal/pull/56) merged; after Android native-window registration, visible CPU HWND now requests actual `NtUserRedrawWindow`, not just stale-surface exposure. Native provider [CI 45105262930](https://github.com/rgarn023/CharoitePortal/actions/runs/45105262930) in progress; patch/source tests pass, ELF/PE not yet verified.
- **Fresh test only:** `v19` one-shot private scratch staged, older v1–v18 preserved and read-only. No v19 APK released, no phone action.
- **Next:** verify provider outputs + matching Java host/Explorer ELF/PE digests before updating signed experimental APK. Require one opt-in v19 Galaxy test to distinguish HWND drawing vs Android TextureView frame. Overall 40% estimated.

## 2026-11-23 — Native surface refresh repaint after repeated Galaxy exit 15

- **Latest user report:** After 1183 test request, another 360×220 visible, registered Android window and exit **15: neither Windows pixel matched**; no Android frame-update event. Screenshot does not show build number. Avoid rerunning any possibly consumed v18 scratch.
- **New actual WineAndroid code change:** Pinned `WM_ANDROID_REFRESH` CPU path now exposes surface **and** requests one real visible-HWND GDI invalidation/update after native surface registration. Previous test EXE-only redraw has not worked; this modification targets the native driver ordering. Keep OpenGL path and strict readback gates unchanged.
- **CI:** Source-only `patch_android_refresh_redraw.py` with exact-match tests, integrated into isolated [Wine29 provider workflow](https://github.com/rgarn023/CharoitePortal/actions/workflows/wine29-first-provider-crossbuild.yml). Native PE/ELF build is pending, **not a verified graphics fix**.
- **Next:** pass CI, inspect compiled driver and matching Java host, package only to a fresh experimental v19 signed release, obtain at most one owner-approved test. No stable Portal data touched; overall readiness estimate stays 40%.

## 2026-11-23 01:42 UTC — Meteorite Alpha build 1183 signed and released

- **Owner-confirmed v17:** 360×220 native window surface reached Android, but neither Win32 client nor screen pixel purple. Exit 15, no Android frame-update checkpoint. v17 consumed; do not repeat.
- **Implemented GDI repair attempt:** Bounded direct HWND client paint on attempts 0/20/60 preserves WM_PAINT and independent purple GetPixel checks. [Desktop Wine 45095286821](https://github.com/rgarn023/CharoitePortal/actions/runs/45095286821) **SUCCESS** with strict exit 42.
- **Official signed experimental release:** [Meteorite Alpha 1183](https://github.com/rgarn023/CharoitePortal/releases/tag/charoite-next-vc1183) published after [Android 45095546802](https://github.com/rgarn023/CharoitePortal/actions/runs/45095546802) **SUCCESS** including signing and publication. New private v18 only, all v1–v17 scratch and old binaries intact. No Galaxy v18 test yet.
- **Next owner gate:** Normal in-app update to 1183 and one v18 window test. Capture Android frame history, Windows 15/16/17/42 exit and last native log on failure. If still 15 with no Android callback, work on underlying native window surface and GDI flush/queue.
- **Stable/safety:** No touch to stable Portal, games, saves, rootfs or user prefixes. Estimated 40% overall readiness until new device evidence.

## Current 2026-11-23 — Galaxy v17 fail and v18 native painting recovery

- **Owner v17:** Status 15 = neither client nor desktop screen pixel purple, despite visible 360×220 window, Android TextureView availability and native surface handoff. No updated Android frame event. v17 consumed; NO reruns.
- **P0 implementation:** [PR #54](https://github.com/rgarn023/CharoitePortal/pull/54) merged, direct GetDC(hwnd)/FillRect/GdiFlush bounded paint fallback. [Desktop Wine 45095286821](https://github.com/rgarn023/CharoitePortal/actions/runs/45095286821) PASS strict both pixels exit 42; exact artifact ZIP and PE hashes verified.
- **P0 Next APK:** [PR #55](https://github.com/rgarn023/CharoitePortal/pull/55) merged, verifies binary and stages fresh v18 scratch in experimental-only app. Static [45095495656](https://github.com/rgarn023/CharoitePortal/actions/runs/45095495656) PASS. Signed [Android workflow 45095546802](https://github.com/rgarn023/CharoitePortal/actions/runs/45095546802) IN PROGRESS, release pending.
- **Then:** only after official signed release, one Galaxy v18 test; check both Win32 status and Android frame history. If no frame still, trace GDI surface allocation/dirty flush and native buffer queue in pinned driver; avoid useless repeat phone diagnostics. Stable Portal and user data preserved. Estimated 40%.

## 2026-11-23 01:38 UTC — Next release candidate v18 GDI paint recovery

- **Verified owner result v17:** Exit **15**, neither Windows client nor screen DC purple. Android 360×220 surface registered but no frame-update checkpoint. Do not repeat v17.
- **Actual source change:** [PR #54](https://github.com/rgarn023/CharoitePortal/pull/54) merged, bounded Windows GDI GetDC/FillRect/GdiFlush recovery only 3/100 attempts, preserves strict dual-pixel proof.
- **Desktop Wine** [45095286821](https://github.com/rgarn023/CharoitePortal/actions/runs/45095286821) **SUCCESS**, exact verified source-built fixture artifact ZIP sha256 `05f4d80c56312ef9fdd567cce61c3c939e21b047a5bf9a3ec469c6c6545e08c8`, PE sha256 `80c1df49ed02b61aa4bf479b7fc6805a258a24e1559cf7e0408a19c1a72eb670`.
- **Experimental candidate:** source stage and isolated **v18** scratch; signed Android build and Galaxy verification **PENDING**. Next: source tests → signed APK + hashes → one Galaxy v18 test, preserve all history. Estimated 40%.

## 2026-11-23 01:33 UTC — v17 failure directs direct GDI repaint recovery

- **On-device v17 verified:** hwnd 0x2003e 360×220 visible/drawable, Android `SurfaceTexture` available, WineAndroid surface registered. **Exit 15 = neither Windows client nor desktop screen pixel matched**. No reported Android frame-update event. Do not reuse v17.
- **P0 implementation:** Source-only x64 GUI fixture now retries direct `GetDC(hwnd)`/GDI `FillRect` on bounded attempts 0, 20, 60, alongside existing WM_PAINT/UpdateWindow path. Never bypass the independent two-purple-pixel + visible-window exit 42 gate. Desktop CI pending.
- **Then:** prove desktop build and hashes, new v18 one-shot scratch, signed separate experimental release, one opted-in Galaxy test. If failure persists, focus WineAndroid `pCreateWindowSurface`/GDI dirty flush and buffer queue rather than reiterating generic logs. Overall readiness ~40%; no stable/user data touched.

## 2026-11-23 00:51 UTC — Public build 1179 signed, v17 Galaxy evidence required

- **Screen awake confirmed:** owner reports no sleep while active in experimental Portal; foreground-only `FLAG_KEEP_SCREEN_ON` feature is working on Galaxy.
- **Desktop source proven:** x64 dual-readback fixture passed [Wine run 45090425972](https://github.com/rgarn023/CharoitePortal/actions/runs/45090425972) with exit 42 and verified ZIP/PE SHA-256 artifact hashes.
- **Experimental release confirmed:** [Meteorite Alpha 1179](https://github.com/rgarn023/CharoitePortal/releases/tag/charoite-next-vc1179) published with signed APK, [Android Actions 45090730363](https://github.com/rgarn023/CharoitePortal/actions/runs/45090730363) **SUCCESS** (build and publication). Includes **fresh private v17 window test**, Android 20-event presentation record, and 15/16/17/42 diagnostics. APK installation/on-device graphics are **not** yet verified.
- **Next (owner action):** one normal in-app update and one isolated v17 test; send Wine29 display check and v17 window log. No repetitive phone testing. If client-only purple (16), focus screen readback/compositing; if neither (15), focus paint/flush and whether Android receives a posted frame.
- **Safety and readiness:** v1–v16 scratch, stable Portal, user games/saves/prefixes/rootfs untouched; v1.0 readiness estimated ~40%.

## 2026-11-23 00:47 UTC — v17 fixture packaged in source, full Android CI running

- **No sleep:** foreground keep-screen-on behavior observed successful by owner on Galaxy.
- **Exact fixture:** [desktop run 45090425972](https://github.com/rgarn023/CharoitePortal/actions/runs/45090425972) **SUCCESS**; artifact ZIP `f82c963c8de53429c889c6338c27e1091889838e96e2bed0403b0973bbf5c226`; PE `c8f19ccfc4804029837589def8c500d1f41ff071d2f91153dc6b8aff66b5f727`. Strict exit 42 still requires client+screen readback and visible HWND.
- **v17 integration:** [PR #53](https://github.com/rgarn023/CharoitePortal/pull/53) merged [4080e5fa](https://github.com/rgarn023/CharoitePortal/commit/4080e5faa9f78ac873f5b74525169b57b124e731); bounded Android frame events and exit 15/16/17 explanation, new private one-shot v17 only. [Static run 45090684361](https://github.com/rgarn023/CharoitePortal/actions/runs/45090684361) **PASS**; [signed Android run 45090730363](https://github.com/rgarn023/CharoitePortal/actions/runs/45090730363) **RUNNING**. Do not claim a release or Android purple pixels yet.
- **Next:** verify full build and release; one owner-approved v17 Galaxy test; use separate Android texture evidence to distinguish actual presentation. Preserve all consumed scratch. Estimated completion 40%.

## 2026-11-23 00:45 UTC — v17 discriminating graphics gate

- **Owner-confirmed UX:** no-sleep while foreground in Meteorite Alpha works on Galaxy. No further UX change needed.
- **Verified desktop fixture:** [Wine CI 45090425972](https://github.com/rgarn023/CharoitePortal/actions/runs/45090425972) **SUCCESS**, strict dual-pixel exit 42. Artifact 14780807305 ZIP digest `f82c963c8de53429c889c6338c27e1091889838e96e2bed0403b0973bbf5c226`, internal PE `c8f19ccfc4804029837589def8c500d1f41ff071d2f91153dc6b8aff66b5f727` independently verified.
- **In progress Android v17:** Pin both hashes into experimental signed workflow, launch from **fresh private v17** scratch, collect bounded Android TextureView event history, and give diagnostic meanings for exits 15 (neither pixel), 16 (client only), 17 (screen only), 42 (both). Strict pass remains unchanged. Android CI and Galaxy runtime not yet verified.
- **Next:** green source-only tests → signed APK → single authorized v17 Galaxy check. No historical scratch reuse or stable Portal data access. Overall 1.0 estimated 40%.

## 2026-11-23 00:41 UTC — Galaxy confirmation and discriminating paint fixture

- **Confirmed device UX:** Owner reports "No sleep" — Meteorite Alpha foreground screen awake works on Galaxy; no need to change device power settings.
- **P0 rendering:** 360×220 window creation and surface registration observed; native posted purple frame remains unverified. Do not count this as a graphics pass.
- **Source-only next test:** x64 fixture now samples HWND client DC and desktop DC separately. Exit 42 still requires both purple and visible; exits 15/16/17 identify neither/client-only/screen-only. Desktop Wine CI must pass before new pinned fixture artifact is staged in fresh v17 scratch. Do not rerun any previously executed one-shot scratch.
- **Overall:** ~40% estimated.

## 2026-11-23 00:35 UTC — Build 1175 signed and released, Galaxy test pending

- **P0 screen awake RELEASED in experimental Next:** [Meteorite Alpha 1175](https://github.com/rgarn023/CharoitePortal/releases/tag/charoite-next-vc1175), [Actions 45089079910](https://github.com/rgarn023/CharoitePortal/actions/runs/45089079910) **SUCCESS**. Foreground activity `FLAG_KEEP_SCREEN_ON` enabled, cleared on pause, no persistent wake lock. Actual device behavior pending.
- **P0 rendering v16 RELEASED, not runtime verified:** Verified new WineAndroid host/Explorer assets packaged with exact ZIP hashes; fresh private window-v16 test avoids historical scratch. One owner-authorized Galaxy test needed; obtain screenshot/exit and last bounded v16 log. Previous evidence shows 360×220 native surface registration but exit 15, not a purple-pixel pass.
- **Next after device evidence:** If no Android `TextureView` frame callback, trace native `android_surface_flush`, buffer lock/post error status and WM_PAINT. If Android RGB is purple yet Win32 screen-DC GetPixel remains invalid, separate presentation pass from readback failure; never mark game rendering complete without visible pixels.
- **Progress:** estimated v1.0 40%. Stable Portal, user data and prior scratch untouched.

## 2026-11-23 00:30 UTC — Merged screen-awake and v16 native driver

- **P0 foreground screen awake:** [PR #51](https://github.com/rgarn023/CharoitePortal/pull/51) merged as [d873786d](https://github.com/rgarn023/CharoitePortal/commit/d873786d86145b24ebba737af2c34e03a3d3a671). Experimental-only `CharoiteNextAwakeApplication` keeps each resumed Charoite activity awake and clears flag on pause. No background wake lock; stable Portal unchanged.
- **P0 native graphics:** Matched Wine29 host and Explorer assets from successful provider [45084634107](https://github.com/rgarn023/CharoitePortal/actions/runs/45084634107) have been repinned by exact ZIP SHA-256; the next test uses fresh **v16** scratch, preserving consumed v15. No purple screen readback is yet verified on device.
- **Tests:** Static [45089079934](https://github.com/rgarn023/CharoitePortal/actions/runs/45089079934) **SUCCESS**. Signed [Android 45089079910](https://github.com/rgarn023/CharoitePortal/actions/runs/45089079910) **RUNNING**, release not yet verified. Verify signature/install/update and native artifact hashes before requesting one v16 Galaxy test.
- **Overall:** ~40% estimated. No phone tests or game/prefix modifications in this development session.

## 2026-11-23 00:26 UTC — Next experimental release candidate

- **P0 screen awake:** [PR #51](https://github.com/rgarn023/CharoitePortal/pull/51) adds experimental-only `CharoiteNextAwakeApplication` using resumed-activity `FLAG_KEEP_SCREEN_ON` and pause-time cleanup. No background wake lock, stable package changes or settings permission.
- **P0 graphics v16:** Provider [45084634107](https://github.com/rgarn023/CharoitePortal/actions/runs/45084634107) **SUCCESS**, postbuild [45085211043](https://github.com/rgarn023/CharoitePortal/actions/runs/45085211043) **SUCCESS**. Next APK workflow repins matching host/explorer ZIP hashes from that run and stages a **fresh, non-reusable `x64-window-v16` scratch**. Desktop fixture's strict purple-pixel gate remains. Actual Android rendering **NOT VERIFIED**.
- **CI gate:** Run static contracts and signed Next-only APK build; do not claim v16 shipped until official release and APK published. Request one Galaxy v16 test after update; never repeat consumed v15.
- **Completion:** Estimated 40%; without a verified on-device purple frame, unchanged.

## 2026-11-22 — Sleep prevention and Galaxy window trace

- **Requested foreground screen-awake behavior:** experimental-only `CharoiteNextAwakeApplication` installs callbacks for every resumed Charoite activity, adds `FLAG_KEEP_SCREEN_ON`, and clears on pause. This covers main Portal/boot, setup/gameplay, and the separate Wine29 test process; no persistent wake lock or stable Portal modification. Source-only tests pending CI.
- **Rendering:** Galaxy build 1169 window test still exits **15**, after 1440×2581 desktop dimensions and x64 360×220 surface registration. Android visible purple frame and Win32 screen pixel are not verified. Do not reuse consumed v15 scratch.
- **Native driver:** [provider CI 45084634107](https://github.com/rgarn023/CharoitePortal/actions/runs/45084634107) **SUCCESS** with [postbuild 45085211043](https://github.com/rgarn023/CharoitePortal/actions/runs/45085211043) **SUCCESS**. Next graphics batch must verify pinned manifest hashes, stage the new driver into a fresh versioned experimental build, and use one authorized phone test. Build 1169 does not carry this native patch.
- **Readiness:** ~40%, not a gameplay or rendering success.

## 2026-11-22 23:42 UTC — Graphics P0 native flush work merged

- **P0 graphics:** [PR #50](https://github.com/rgarn023/CharoitePortal/pull/50) merged as [6ef18241](https://github.com/rgarn023/CharoitePortal/commit/6ef18241cf8e0e01a0f8c3fb3c1064246d22de31). Native Android CPU surface flush now fails closed on missing window, lock error, or post error, with bounded Wine WARN status. Workflow source-only offline test step PASSED. [Provider cross-build 45084634107](https://github.com/rgarn023/CharoitePortal/actions/runs/45084634107) **RUNNING**; no PE/ELF or on-device pass is claimed.
- **P0 device gate:** Signed [Meteorite Alpha 1169](https://github.com/rgarn023/CharoitePortal/releases/tag/charoite-next-vc1169) [Android 45077167201](https://github.com/rgarn023/CharoitePortal/actions/runs/45077167201) **PASSED**. Run exactly one new isolated v15 window test on owner's Galaxy when authorized, then inspect preserved Android TextureView frame sample vs strict Win32 screen-DC GetPixel. This release does *not* include source-only PR #50.
- **Independent blocker:** [Source audit 45084581615](https://github.com/rgarn023/CharoitePortal/actions/runs/45084581615) passed all source tests but its historical original artifact download failed ("no artifact matches"). Do not count entire audit as passing or rebuild/overwrite consumed scratch to compensate.
- **Next action (engineering):** Verify provider workflow compile and manifest before packaging another experimental driver update. No additional phone reruns or historical prefix modification. Estimated v1.0 readiness **40%**, not audited.

## Native Android frame flush — 2026-11-22

- **P0 Android graphics (source implementation):** The pinned Wine29 CPU `android_surface_flush` path ignored a failed `NATIVE_WINDOW_UNLOCK_AND_POST` and reported successful flush on an unsuccessful `NATIVE_WINDOW_LOCK`. A fail-closed source patch on `fix/wine29-android-surface-flush-gate` now propagates errors through FALSE and emits bounded Wine WARN markers. Exact-anchor source-only regression tests and provider-workflow integration have been committed; native provider CI / Galaxy verification are pending. Not a verified rendering fix.
- **Signed current build:** Meteorite Alpha [1169](https://github.com/rgarn023/CharoitePortal/releases/tag/charoite-next-vc1169), [GitHub Actions 45077167201](https://github.com/rgarn023/CharoitePortal/actions/runs/45077167201) PASSED. The v15 Galaxy purple-frame check has not yet been run/verified.
- **Next:** Inspect provider CI (actual artifact hashes, source patch gate, Android ELF and Windows PE), then decide whether native driver should be pinned into a new APK. Preserve strict Win32 GetPixel test and all old evidence. Never test or modify stable Portal/user data/historical scratch.
- **Overall:** 40% estimated; only increase with runtime evidence.

## Active graphics integration update — 2026-11-22

- **v15 source merged:** [PR #49](https://github.com/rgarn023/CharoitePortal/pull/49) improves Android child-window frame proof and isolates the next test in new v15 scratch. Static PR CI [45077079556](https://github.com/rgarn023/CharoitePortal/actions/runs/45077079556) passed; full [Android build 45077167201](https://github.com/rgarn023/CharoitePortal/actions/runs/45077167201) is pending.
- **Highest unblocked gate:** confirm signed build/release, then user-authorized Galaxy test of **native purple Android frame versus Win32 GetPixel(screen)**. Do not count either as passed until directly observed.
- **Estimated readiness:** 40%. No fresh device test until the release is verified; never reuse v14 or older consumed scratch.

## Current graphics priority — 2026-11-22

- **P0, actively progressing:** Galaxy v14 x64 fixture reached native Android registration of a 360×220 window; the Win32 screen-DC pixel test still exited 15. No Galaxy visual/purple-pixel pass has been verified.
- **P0, proposed on `fix/wine29-galaxy-frame-proof-v15`:** Verify actual **Android TextureView presentation** after a posted child frame, using a bounded 64×64 readback and first-frame/purple-color checkpoint. The Win32 screen-DC test remains strict and separate. Pending lightweight CI and an explicitly authorized future Galaxy test; this change is not a rendering success claim.
- **P1, if Android reports a posted nonpurple frame:** inspect the native `android_surface_flush` / buffer queue and paint path with bounded evidence rather than guessing. If Android reports purple but Win32 `GetPixel(screen)` remains invalid, investigate the screen-DC readback separately.
- **Isolation:** all source work targets experimental Meteorite Alpha. Do not reuse consumed v1–v14 window scratch or touch stable Portal, saves, prefixes, games, or rootfs. Readiness stays approximately **40%** until runtime proof improves.

# Charoite Portal — Development Queue

**Scope:** experimental Wine29 source-only provider work on `main`. Updated 2026-11-12. Queue entries are priorities, not claims of completed tests.

| Priority | Task | State | Exit evidence / next action |
| --- | --- | --- | --- |
| P0 | Verify latest five-module workflow run(s) and `batch-import-closure.json` | **WAITING FOR EVIDENCE** | Retrieve actual run ID, job conclusion, artifact manifests and import table; investigate failures with logs; do not assume pass |
| P0 | Resolve candidate PE import dependencies | **IN PROGRESS** | Track `mouhid.sys`, `hidclass.sys`, `hidparse.sys`, `winehid.sys`, `winexinput.sys`; compare external imports to verified sealed module set; distinguish unresolved imports |
| P1 | Build `mscms.dll` with pinned LCMS2 dependencies | **NOT STARTED** | Pin dependency, verify license/build, ARM64 PE header and imports in source-only CI |
| P1 | Build `winebth.sys`, `winebus.sys`, `wineusb.sys` | **NOT STARTED** | Confirm Android/Bionic Unix companion availability and build closure; PE-only output is insufficient |
| P1 | Build bounded, automated provider-closure report | **IN PROGRESS — postbuild static validation committed** | Report per-module source hashes, PE machine, ordinary/delay imports, missing providers, native companions, provenance and explicit unverified runtime |
| P2 | Integrate fully verified modules into isolated NEW Wine29 scratch | **BLOCKED** | Requires full dependency closure and owner approval for new runtime/phone test |
| P2 | Validate Wine29 prefix bootstrap, RpcSs, and installer functionality | **BLOCKED** | Requires opt-in, fresh scratch only, controlled logs and non-destructive tests |
| P3 | Portal/Next integration, UX and gameplay regression | **BLOCKED** | Requires working runtime and owner-authorized device test |

## Automated verification update (2026-11-12)
- [Postbuild workflow hardening a6b04d0](https://github.com/rgarn023/CharoitePortal/commit/a6b04d0bd0f3e7470e3886ee02dafdda0f73c746) adds read-only artifact provenance, ZIP limits, PE header/hash and candidate import-partition consistency checks. It runs on matching cross-build completion events. **Committed only; postbuild job success has not been independently verified.**
- Next: verify an actual postbuild run and its upstream artifact; investigate any failure before extending providers. No owner action required.


- [Source inventory commit 97f2504](https://github.com/rgarn023/CharoitePortal/commit/97f25042c015b7d8017add554a34a5b72823822c) adds a source-only Makefile inventory for `mscms.dll`, `winebth.sys`, `winebus.sys`, `wineusb.sys` to the existing cross-build job. **No modules compiled by this change; CI result unverified.**


- [Build probe 7065f8c](https://github.com/rgarn023/CharoitePortal/commit/7065f8c183596244f17b8e71bee82a52c8f2abf5) and [PE-header gate 91bbcc8](https://github.com/rgarn023/CharoitePortal/commit/91bbcc82b20851cae36a26f230d83ad4c33a7700) now attempt bounded source-only PE cross-builds of the four remaining providers (`mscms.dll`, `winebth.sys`, `winebus.sys`, `wineusb.sys`) in CI after the existing five-module build. Each attempt records bounded logs and only copies a candidate with a readable PE header; failures are nonblocking to preserve established evidence. **No probe run results verified yet; no added module counted as built.**

- [Probe manifest commit 47f4893](https://github.com/rgarn023/CharoitePortal/commit/47f48935fcf7c605ffa7b73c89790890734a7254) now gates each of four remaining provider build probes on actual ARM64 PE signature/machine and emits SHA-256, size, source provenance and explicit unverified closure flags. Bounded logs and per-module status are preserved. **Build execution and module success remain unverified.**

## Known evidence (do not overstate)
- [Three-module CI run #43247190822](https://github.com/rgarn023/CharoitePortal/actions/runs/43247190822) **SUCCESS**; `mouhid.sys`, `hidclass.sys` and supporting `hidparse.sys` built/inspected as ARM64 PE. Two of eight original missing provider modules source-built; **0/8 full closure verified**.
- Five-module expansion [commit 1c33328](https://github.com/rgarn023/CharoitePortal/commit/1c333282a0b32acb0f1fc3cc937b7057ef590a44). Owner screenshot suggested workflow #13 success, but run/job/artifact evidence was not independently inspected.
- [Batch import report commit 6e07661](https://github.com/rgarn023/CharoitePortal/commit/6e076612d9d40f58d2848ab7644bb2a1e3f23ab9) and [Actions summary fix 7e131c2](https://github.com/rgarn023/CharoitePortal/commit/7e131c2001e2454d531792e3557a825698bc6096) **committed, not yet run-verified**.
- [Issue #7](https://github.com/rgarn023/CharoitePortal/issues/7) enumerates original eight: `mscms.dll`, `hidclass.sys`, `mouhid.sys`, `winebth.sys`, `winebus.sys`, `winehid.sys`, `wineusb.sys`, `winexinput.sys`. `hidparse.sys` is supporting dependency.

## Session discipline
- Work through multiple safe tasks per active ChatGPT session, then update this queue and [CURRENT_HANDOFF.md](CURRENT_HANDOFF.md).
- No routine owner notifications; only ask for permission, access, APK installation, or testing when truly necessary.
- Avoid repeated source-only workflow commits merely to trigger a run. Diagnose failed runs before modifying CI.
- Never modify or access stable app data, user games/saves, consumed Wine29 generations or historical scratch.
