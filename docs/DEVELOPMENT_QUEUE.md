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
