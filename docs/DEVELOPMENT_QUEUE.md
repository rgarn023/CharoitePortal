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
